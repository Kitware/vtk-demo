"""Partition count showcase in trame-pyvista's SimpleViewer: VTK.wasm or server rendering.

The voxel island of the glyph, actor and composite worlds, drawn from a single
vtkPartitionedDataSetCollection by a single actor and a
vtkCompositePolyDataMapper, cut into as many partitions as asked for. The
island has 43,132 meshes (terrain columns, tree trunks, tree crowns, wind
arrows and cloud puffs). They are listed in a fixed order and split into
``--partitions`` consecutive groups of (nearly) equal mesh count, each group
baked into one partition. With 1 partition the whole island is one polydata;
with 43,132 every mesh is its own partition. The triangles stay the same, only
the number of blocks the mapper has to draw changes.

Every mesh carries the same point arrays (normals and an RGB color) so that
partitions mixing several kinds of objects stay consistent, and so that every
partition count draws exactly the same vertex data.

    vtk-demo run trame.partition-world                       # VTK.wasm on WebGL 2
    vtk-demo run trame.partition-world --partitions 43132    # one partition per mesh
    vtk-demo run trame.partition-world --webgpu              # WebGPU in the browser and on the server
"""

import os
import sys

from vtk_demo.scenes import build_partitioned_island

from .common import run_simple_viewer, vuetify_theme

THEME = vuetify_theme(primary="#6a1b9a", background="#e3f2fd", surface="#ffffff")

# Python wrappers of the partitions' VTK objects, see merge_instances()
_WRAPPERS = []


def add_arguments(parser):
    parser.add_argument(
        "--partitions",
        type=int,
        default=100,
        metavar="N",
        help="Number of partitions to split the island into, 1 up to one per "
        "mesh (default: 100; larger values are clamped to the mesh count)",
    )


def build(renderer, args):
    if args.partitions < 1:
        raise SystemExit("error: --partitions must be at least 1")
    n_partitions, n_meshes, n_triangles = build_partitioned_island(
        renderer, args.partitions, keep_alive=_WRAPPERS
    )
    return (
        f"{n_partitions:,} partitions · {n_meshes:,} meshes · {n_triangles:,} triangles"
    )


def main():
    run_simple_viewer(
        "partition_world", "Partition count showcase", THEME, build, add_arguments
    )

    # Releasing _WRAPPERS at interpreter shutdown hits the slow path described in
    # merge_instances(): minutes at 43k partitions. There is nothing left to clean up.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    main()
