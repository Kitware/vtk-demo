"""Composite dataset showcase in trame-pyvista's SimpleViewer: VTK.wasm or server rendering.

An archipelago of the voxel island from the glyph and actor worlds, drawn
from a single vtkPartitionedDataSetCollection by a single actor and a
vtkCompositePolyDataMapper. Each island is a partitioned dataset whose
partitions are its terrain columns, tree trunks, tree crowns, wind arrows and
cloud puffs. Every object is baked into its partition's mesh (transform
applied, color stored as a per point RGB array), so each partition is one
plain polydata. The islands are copies of the same world scattered at random
X and Y offsets: they share their connectivity and only differ by their points.

    vtk-demo run trame.composite-world                # VTK.wasm on WebGL 2
    vtk-demo run trame.composite-world --worlds 9     # a bigger archipelago
    vtk-demo run trame.composite-world --webgpu       # WebGPU in the browser and on the server
"""

from vtk_demo.scenes import build_archipelago

from .common import run_simple_viewer, vuetify_theme

THEME = vuetify_theme(primary="#00838f", background="#e3f2fd", surface="#ffffff")


def add_arguments(parser):
    parser.add_argument(
        "--worlds",
        type=int,
        default=4,
        metavar="N",
        help="Number of islands to scatter (default: 4)",
    )


def build(renderer, args):
    if args.worlds < 1:
        raise SystemExit("error: --worlds must be at least 1")
    n_partitions, n_triangles = build_archipelago(renderer, args.worlds)
    return (
        f"{args.worlds} islands · {n_partitions} partitions · {n_triangles:,} triangles"
    )


def main():
    run_simple_viewer(
        "composite_world", "Composite dataset showcase", THEME, build, add_arguments
    )


if __name__ == "__main__":
    main()
