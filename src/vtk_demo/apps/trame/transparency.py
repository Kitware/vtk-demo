"""Transparency showcase in trame-pyvista's SimpleViewer: VTK.wasm or server rendering.

An opaque gold knot trapped inside nested translucent shells, circled by a
ring of overlapping tinted glass cubes, with soap bubbles drifting above a
see-through floor. Almost every actor is translucent and many of them
overlap, which makes it a good stress test for depth peeling and for how
each backend sorts and blends translucent geometry.

    vtk-demo run trame.transparency             # VTK.wasm on WebGL 2
    vtk-demo run trame.transparency --webgpu    # WebGPU in the browser and on the server
"""

from vtk_demo.scenes import build_transparency_scene

from .common import run_simple_viewer, vuetify_theme

THEME = vuetify_theme(
    primary="#06d6a0", background="#0b1d33", surface="#13294b", dark=True
)


def build(renderer, _args):
    n_translucent, n_actors = build_transparency_scene(renderer)
    return f"{n_translucent} of {n_actors} actors translucent"


def main():
    run_simple_viewer("transparency", "Transparency showcase", THEME, build)


if __name__ == "__main__":
    main()
