"""Glyph showcase in trame-pyvista's SimpleViewer: VTK.wasm or server rendering.

A voxel island made of tens of thousands of instanced boxes, covered in a
forest of trees, swept by a swirling wind drawn with arrows and topped with
puffy clouds. Each layer is a single actor driven by a vtkGlyph3DMapper: one
small source mesh, instanced on the GPU at every point of a point cloud, with
per point scale, orientation and color. That's the fast path for drawing a
lot of objects, and a good stress test for each backend's instancing.

    vtk-demo run trame.glyph             # VTK.wasm on WebGL 2
    vtk-demo run trame.glyph --webgpu    # WebGPU in the browser and on the server
"""

from vtk_demo.scenes import build_glyph_island

from .common import run_simple_viewer, vuetify_theme

THEME = vuetify_theme(primary="#2e7d32", background="#e3f2fd", surface="#ffffff")


def build(renderer, _args):
    n_actors, n_instances, n_triangles = build_glyph_island(renderer)
    return f"{n_instances:,} glyphs · {n_actors} actors · {n_triangles:,} triangles"


def main():
    run_simple_viewer("glyph", "Glyph showcase", THEME, build)


if __name__ == "__main__":
    main()
