"""Many actors showcase in trame-pyvista's SimpleViewer: VTK.wasm or server rendering.

The very same voxel island as the glyph world, but built the naive way:
one actor per object instead of one glyph mapper per layer. Every terrain
column, tree trunk, tree crown, wind arrow and cloud puff is its own actor
with its own transform and color. Actors of the same kind share one mapper
and one source mesh, so the geometry is only stored (and shipped to the
browser) once. What's left is the per actor cost: tens of thousands of
actors to synchronize, cull and draw one by one. Compare it with the glyph
world to see what GPU instancing saves.

    vtk-demo run trame.actor-world             # VTK.wasm on WebGL 2
    vtk-demo run trame.actor-world --webgpu    # WebGPU in the browser and on the server
"""

from vtk_demo.scenes import build_actor_island

from .common import run_simple_viewer, vuetify_theme

THEME = vuetify_theme(primary="#c62828", background="#e3f2fd", surface="#ffffff")


def build(renderer, _args):
    n_actors, n_triangles = build_actor_island(renderer)
    return f"{n_actors:,} actors · {n_triangles:,} triangles"


def main():
    run_simple_viewer("actor_world", "Many actors showcase", THEME, build)


if __name__ == "__main__":
    main()
