"""Animation streaming: Python updates a field, VTK.wasm renders it in the browser.

A wave equation is stepped in numpy on the server. Each step only modifies the
points and scalars of a PyVista mesh, so only those two arrays are pushed to
the browser: the connectivity, the actor, the colormap… are already there.
Orbit the camera while it runs: interaction stays fully client side.

    vtk-demo run trame.animation                                 # VTK.wasm on WebGL 2
    vtk-demo run trame.animation --resolution 1024 --webgpu      # same thing on WebGPU
"""

import asyncio
import time

import pyvista as pv
from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import pyvista as pvw
from trame.widgets import vuetify3 as v3

from vtk_demo.pyvista_adapter import add_scene
from vtk_demo.scenes import build_wave_scene

from . import observability as obs


class AnimationDemo(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")
        cli = self.server.cli
        cli.add_argument(
            "--resolution",
            type=int,
            default=256,
            metavar="N",
            help="Grid points per side of the simulated surface (default: 256)",
        )
        obs.add_arguments(cli)
        args, _ = cli.parse_known_args()
        self.rendering = obs.select_backend()  # before the render window is created

        self.plotter = pv.Plotter(off_screen=True)
        server_backend = obs.check_server_backend(self.plotter.render_window)
        self.obs = obs.Observability(
            self.server,
            "animation",
            self.rendering,
            server_backend,
            self.plotter.render_window,
        )
        self.surface = add_scene(self.plotter, build_wave_scene, args.resolution)

        self.state.update(
            dict(
                running=True,
                step=0,
                steps_per_s=0,
                n_cells=self.surface.mesh.number_of_cells,
            )
        )
        self._task = None
        self._client_done = asyncio.Event()
        self._update_id = 0  # matches each client "updated" event to its update
        self._build_ui()
        self.ctrl.on_server_ready.add(self._start)

    def _start(self, **_):
        if self.state.running and self._task is None:
            self._task = asyncio.create_task(self._run())

    @change("running")
    def _on_running(self, running, **_):
        if running:
            self._start()

    async def _run(self):
        t_last, steps = time.perf_counter(), 0
        try:
            while self.state.running:
                # Drop the arrays no state references anymore (the previous steps),
                # or the server grows ~1 MB/step
                self.ctx.view.object_manager.PruneUnusedBlobs()

                t_step = time.perf_counter()
                # Only the points and scalars change: they are the only thing sent over
                self.surface.advance()

                # Clear event and trigger sync
                self._client_done.clear()
                self._update_id += 1
                self.ctx.view.update(update_id=self._update_id)

                # The browser fetches the new states then their arrays in separate
                # requests: changing the mesh in between makes it receive states
                # referring to arrays it did not get. Wait for it to be done.
                try:
                    await asyncio.wait_for(self._client_done.wait(), timeout=2)
                except TimeoutError:
                    print("timeout")
                    pass  # view not ready yet, or update dropped: move on

                steps += 1
                now = time.perf_counter()
                with self.state:
                    self.state.step = self.surface.steps
                    if now - t_last > 1:
                        self.state.steps_per_s = round(steps / (now - t_last))
                        t_last, steps = now, 0
                await asyncio.sleep(max(0, 1 / 25 - (now - t_step)))
        finally:
            self._task = None

    def _on_client_updated(self, update_id=None):
        # The view also emits "updated" once on mount, and late for an update we
        # stopped waiting for: only the one for the latest update counts
        if update_id == self._update_id:
            self._client_done.set()

    def _build_ui(self):
        self.state.trame__title = "VTK.wasm animation"
        with VAppLayout(self.server, theme="dark") as self.ui:
            with v3.VMain(classes="position-relative"):
                view = pvw.PyVistaWasmView(
                    self.plotter,
                    ctx_name="view",
                    config=(f"{{ rendering: '{self.rendering}', exec: 'async' }}",),
                    throttle_rate=60,
                    # Past steps are never shown again: only keep the arrays in use
                    cache_size=10,
                )
                # Every update re-applies all the registered states, the interactor's
                # included, which drops mouse presses arriving meanwhile. Its state
                # never changes, so drop it once applied. Do it after each update: the
                # view registers it again when mounted (invoke of GetInteractor).
                interactor_id = view.object_manager.GetId(
                    self.plotter.render_window.GetInteractor()
                )
                session = f"trame.refs['{view.ref_name}'].getRemoteSession()"
                view.updated = (
                    f"{obs.SCENE_READY};"  # only the first call counts
                    f"{session}.native.unRegisterState({interactor_id});"  # FIXME - https://gitlab.kitware.com/vtk/vtk/-/work_items/20204
                    f"trigger('{self.server.trigger_name(self._on_client_updated)}', [], $event)"
                )
                pvw.PyVistaPlotterControls(view)
                self.obs.watch_mode("false")  # always rendered locally
                with v3.VCard(
                    style="position: absolute; top: 1rem; right: 1rem;",
                    classes="d-flex align-center ga-2 pa-2",
                ):
                    v3.VBtn(
                        icon=("running ? 'mdi-pause' : 'mdi-play'",),
                        click="running = !running",
                        density="compact",
                        variant="text",
                    )
                    v3.VLabel(
                        f"{self.rendering} · {{{{ n_cells.toLocaleString() }}}} triangles"
                        " · step {{ step }} · {{ steps_per_s }} updates/s"
                    )


def main():
    AnimationDemo().server.start()


if __name__ == "__main__":
    main()
