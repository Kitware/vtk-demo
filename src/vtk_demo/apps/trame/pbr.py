"""PBR showcase in trame-pyvista's SimpleViewer: VTK.wasm or server rendering, one toggle.

A gold Lucy statue on a marble pedestal, surrounded by a ring of material
spheres (metals and plastics, smooth to rough), clear-coated and brushed
knots, all lit by image based lighting from a skybox. Everything is a plain
PyVista plotter; SimpleViewer adds the toolbar and the switch between
client side (VTK.wasm) and server side rendering of the very same scene.

PBR shaders are only available in VTK.wasm's WebGL backend for now. With
--webgpu the scene still loads, but VTK's WebGPU backend shades it with plain
Phong: no environment reflections and no base color texture.

    vtk-demo run trame.pbr             # VTK.wasm on WebGL 2
    vtk-demo run trame.pbr --webgpu    # WebGPU in the browser and on the server (no PBR)
"""

from vtk_demo.scenes import build_pbr_scene

from .common import run_simple_viewer, vuetify_theme

THEME = vuetify_theme(background="#90CAF9", surface="#BBDEFB")


def build(renderer, _args):
    return f"{build_pbr_scene(renderer):,} triangles"


def main():
    run_simple_viewer("pbr", "PBR showcase", THEME, build)


if __name__ == "__main__":
    main()
