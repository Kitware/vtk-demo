"""Pieces shared by the trame demos."""

import argparse

import pyvista as pv

from vtk_demo.pyvista_adapter import add_scene

from . import observability as obs


def vuetify_theme(primary=None, background=None, surface=None, dark=False):
    """Vuetify config defining a theme named "custom"."""
    colors = {"background": background, "surface": surface, "primary": primary}
    colors = {k: v for k, v in colors.items() if v is not None}
    return {"theme": {"themes": {"custom": {"dark": dark, "colors": colors}}}}


def parse_known_args(add_arguments=None):
    """Parse the arguments ``add_arguments(parser)`` defines, ignoring the others.

    The scene is built before the trame server exists, so the demo specific
    arguments are read early; they are added to ``server.cli`` later on so that
    ``--help`` lists them.
    """
    parser = argparse.ArgumentParser(add_help=False)
    if add_arguments:
        add_arguments(parser)
    return parser.parse_known_args()[0]


def run_simple_viewer(demo, title, vuetify_config, build, add_arguments=None):
    """Show a scene in trame-pyvista's SimpleViewer and start the server.

    The viewer toggles between client side (VTK.wasm) and server side rendering
    of the very same plotter. ``build(renderer, args)`` fills the plotter's
    renderer (see :mod:`vtk_demo.scenes`) and returns a short statistics string, shown in a chip with the active backend.
    ``--webgpu`` (see :mod:`.observability`) picks the rendering API for both
    sides, and the observability HUD reports first frame and interaction times.
    """
    from trame.widgets import vuetify3 as v3
    from trame_pyvista.apps import SimpleViewer

    pv.OFF_SCREEN = True
    args = parse_known_args(add_arguments)
    rendering = obs.select_backend()  # before the render window is created
    plotter = pv.Plotter()
    server_backend = obs.check_server_backend(plotter.render_window, rendering)
    stats = add_scene(plotter, build, args)
    viewer = SimpleViewer(plotter, theme="custom", vuetify_config=vuetify_config)

    # Command line arguments parsed above and by obs, for --help
    if add_arguments:
        add_arguments(viewer.server.cli)
    obs.add_arguments(viewer.server.cli)

    viewer.view_wasm.config = (f"{{ rendering: '{rendering}', exec: 'async' }}",)
    obs.observe_simple_viewer(viewer, demo, rendering, server_backend)

    viewer.state.trame__title = title
    label = (
        f"{viewer.RENDERING_MODE} === 'local'"
        f" ? 'VTK.wasm · {rendering} · {stats}'"
        f" : 'Server · {server_backend} · {stats}'"
    )
    with viewer.ui:
        v3.VChip(
            text=(label,),
            style="position: absolute; top: 1rem; right: 1rem; z-index: 1;",
            variant="flat",
            color="primary",
        )

    viewer.server.start()
    return viewer
