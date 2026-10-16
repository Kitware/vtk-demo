"""PBR showcase in PyVista's original trame UI: vtk.js or server rendering, one toggle.

Same scene as the PBR showcase, but displayed with ``plotter_ui`` from
trame-pyvista: the classic PyVista toolbar whose switch toggles between
client side rendering with vtk.js (scene serialized by trame-vtk) and server
side rendering. Handy to compare against the VTK.wasm path of trame.pbr.

    vtk-demo run trame.pbr-legacy
"""

import pyvista as pv
from trame.app import get_server
from trame.ui.vuetify3 import VAppLayout
from trame.widgets import vuetify3 as v3
from trame_pyvista.ui import get_viewer, plotter_ui

from vtk_demo.pyvista_adapter import add_scene
from vtk_demo.scenes import build_pbr_scene

from . import observability as obs
from .pbr import THEME


def main():
    pv.OFF_SCREEN = True
    plotter = pv.Plotter()
    server_backend = obs.check_server_backend(plotter.render_window, "webgl")
    n_triangles = add_scene(plotter, build_pbr_scene)

    server = get_server(client_type="vue3")
    obs.add_arguments(server.cli, webgpu=False)
    observability = obs.Observability(
        server, "pbr_legacy", "webgl", server_backend, plotter.render_window
    )
    server.state.trame__title = "PBR showcase (vtk.js)"

    with VAppLayout(server, full_height=True, theme="custom", vuetify_config=THEME):
        plotter_ui(plotter, mode="trame", default_server_rendering=False)
        observability.watch_mode(get_viewer(plotter).SERVER_RENDERING)
        # ref of the PyVistaRemoteLocalView created by plotter_ui
        observability.hook_vtkjs(f"view_{plotter._id_name}")

        label = (
            f"{get_viewer(plotter).SERVER_RENDERING}"
            f" ? 'Server · {server_backend} · {n_triangles:,} triangles'"
            f" : 'vtk.js · WebGL · {n_triangles:,} triangles'"
        )
        v3.VChip(
            text=(label,),
            style="position: absolute; top: 1rem; right: 1rem; z-index: 1;",
            variant="flat",
            color="primary",
        )

    server.start()


if __name__ == "__main__":
    main()
