"""Interactive isosurface: VTK filter on the server, VTK.wasm rendering in the browser.

The contour is recomputed in Python when the slider moves; only the new
geometry travels to the browser, where VTK.wasm renders it.
Camera interaction never touches the server.

    vtk-demo run trame.contour             # VTK.wasm on WebGL 2
    vtk-demo run trame.contour --webgpu    # same thing on WebGPU
"""

import pyvista as pv
from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import pyvista as pvw
from trame.widgets import vuetify3 as v3

from vtk_demo.pyvista_adapter import add_scene
from vtk_demo.scenes import build_isosurface_scene

from . import observability as obs


class ContourDemo(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")
        obs.add_arguments(self.server.cli)  # for --help
        self.rendering = obs.select_backend()  # before the render window is created

        self.plotter = pv.Plotter(off_screen=True)
        server_backend = obs.check_server_backend(self.plotter.render_window)
        self.obs = obs.Observability(
            self.server,
            "contour",
            self.rendering,
            server_backend,
            self.plotter.render_window,
            hud_bottom=52,  # above the footer and its slider
        )
        self.iso = add_scene(self.plotter, build_isosurface_scene)

        self.state.update(
            dict(
                data_range=self.iso.data_range,
                contour_value=self.iso.value,
                n_triangles=self.iso.n_triangles,
            )
        )
        self._build_ui()

    @change("contour_value")
    def _on_contour(self, contour_value, **_):
        self.iso.value = contour_value
        self.state.n_triangles = self.iso.n_triangles
        self.ctx.view.render()

    def _build_ui(self):
        self.state.trame__title = "VTK.wasm contour"
        with VAppLayout(self.server) as self.ui:
            with v3.VMain(classes="position-relative"):
                pvw.PyVistaPlotterControls(
                    pvw.PyVistaWasmView(
                        self.plotter,
                        ctx_name="view",
                        config=(f"{{ rendering: '{self.rendering}', exec: 'async' }}",),
                        updated=obs.SCENE_READY,
                    ),
                )
                self.obs.watch_mode("false")  # always rendered locally
                v3.VChip(
                    f"VTK.wasm · {self.rendering} · {{{{ n_triangles.toLocaleString() }}}} triangles",
                    style="position: absolute; top: 1rem; right: 1rem;",
                    variant="outlined",
                )

            with v3.VFooter(app=True, classes="d-flex align-center ga-4"):
                v3.VProgressLinear(
                    indeterminate=True,
                    absolute=True,
                    location="top",
                    active=("trame__busy",),
                )
                v3.VLabel(
                    "Iso value: {{ contour_value.toLocaleString(undefined, { maximumFractionDigits: 1 }) }}",
                    style="width: 10rem;",
                )
                v3.VSlider(
                    v_model="contour_value",
                    min=("data_range[0]",),
                    max=("data_range[1]",),
                    step=("(data_range[1] - data_range[0]) / 255",),
                    hide_details=True,
                    density="compact",
                )


def main():
    ContourDemo().server.start()


if __name__ == "__main__":
    main()
