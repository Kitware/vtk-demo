"""Millions of points: VTK.wasm 64-bit (wasm64) in the browser.

A procedural spiral galaxy is generated with numpy and mirrored into the
browser. wasm64 lifts the 4 GiB address space limit of wasm32, so the client
can hold scenes far larger than a classic WebAssembly module could.

    vtk-demo run trame.galaxy                       # 1M points, wasm64 + WebGL 2
    vtk-demo run trame.galaxy --points 60e6 --webgpu
    vtk-demo run trame.galaxy --wasm32              # compare with classic setup
"""

import time

import pyvista as pv
from trame.app import TrameApp
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import pyvista as pvw
from trame.widgets import vuetify3 as v3

from vtk_demo.pyvista_adapter import add_scene
from vtk_demo.scenes import build_galaxy_scene

from . import observability as obs


class PointCloudDemo(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")
        cli = self.server.cli
        cli.add_argument(
            "--points",
            type=lambda v: int(float(v)),
            default=5_000_000,
            metavar="N",
            help="Number of points, e.g. 20e6 (default: 1M)",
        )
        cli.add_argument(
            "--wasm32", action="store_true", help="Use wasm32 instead of wasm64"
        )
        obs.add_arguments(cli)
        args, _ = cli.parse_known_args()
        self.mode = "wasm32" if args.wasm32 else "wasm64"
        self.rendering = obs.select_backend()  # before the render window is created

        self.plotter = pv.Plotter(off_screen=True)
        server_backend = obs.check_server_backend(self.plotter.render_window)
        self.obs = obs.Observability(
            self.server,
            "galaxy",
            self.rendering,
            server_backend,
            self.plotter.render_window,
        )
        t0 = time.perf_counter()
        add_scene(self.plotter, build_galaxy_scene, args.points)
        print(f"Generated {args.points:,} points in {time.perf_counter() - t0:.1f}s")

        self.state.update(dict(n_points=args.points, sync_ms=None))
        self._t_sync = time.perf_counter()
        self._build_ui()

    def _on_updated(self, *_):
        if self._t_sync is not None:
            self.state.sync_ms = round((time.perf_counter() - self._t_sync) * 1000)
            self._t_sync = None

    def _build_ui(self):
        self.state.trame__title = "VTK.wasm point cloud"
        with VAppLayout(self.server) as self.ui:
            with v3.VMain(classes="position-relative"):
                pvw.PyVistaPlotterControls(
                    pvw.PyVistaWasmView(
                        self.plotter,
                        ctx_name="view",
                        config=(
                            f"{{ mode: '{self.mode}', rendering: '{self.rendering}', exec: 'async' }}",
                        ),
                        progress_enabled=True,
                        progress_delay=200,
                        # Scene loaded: stop the sync timer and report the first frame
                        updated=(
                            f"{obs.SCENE_READY};"
                            f" trigger('{self.server.trigger_name(self._on_updated)}')"
                        ),
                    ),
                )
                self.obs.watch_mode("false")  # always rendered locally
                v3.VChip(
                    f"{self.mode} · {self.rendering} · {{{{ n_points.toLocaleString() }}}} points"
                    " · {{ sync_ms === null ? 'syncing…' : `synced in ${(sync_ms / 1000).toFixed(1)}s` }}",
                    style="position: absolute; top: 1rem; right: 1rem;",
                    variant="outlined",
                )


def main():
    PointCloudDemo().server.start()


if __name__ == "__main__":
    main()
