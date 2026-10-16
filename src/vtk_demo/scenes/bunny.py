"""Smoothed Stanford bunny colored by elevation, with feature edges and a floor."""

import numpy as np
from vtkmodules.vtkFiltersCore import vtkFeatureEdges, vtkSmoothPolyDataFilter
from vtkmodules.vtkFiltersSources import vtkPlaneSource

from . import datasets
from .core import compute_normals, look_from, mesh_actor, set_background


def build_bunny_scene(renderer):
    """Add the bunny scene. Returns the number of triangles of the bunny."""
    smooth = vtkSmoothPolyDataFilter(number_of_iterations=50, relaxation_factor=0.01)
    bunny = compute_normals(smooth(datasets.bunny()))
    bunny.point_data["elevation"] = np.asarray(bunny.points.data)[:, 1]
    edges = vtkFeatureEdges(feature_angle=60, manifold_edges=True, coloring=False)

    set_background(renderer, "#1b1d22")
    renderer.AddActor(
        mesh_actor(bunny, scalars="elevation", cmap="viridis", interpolation="phong")
    )
    renderer.AddActor(mesh_actor(edges(bunny), color="white", line_width=1))
    renderer.AddActor(floor(bunny.bounds, color="#2a2d33", pad=0.5))
    look_from(renderer, (0, 0, 1), (0, 1, 0), azimuth=30, elevation=15)
    return bunny.number_of_cells


def floor(bounds, color, pad=0.0):
    """Unlit plane right under ``bounds`` (y up), ``1 + pad`` times as wide."""
    (x0, x1), (y, _), (z0, z1) = np.reshape(bounds, (3, 2))
    dx, dz = pad * (x1 - x0) / 2, pad * (z1 - z0) / 2
    plane = vtkPlaneSource(
        origin=(x0 - dx, y, z0 - dz),
        point1=(x0 - dx, y, z1 + dz),
        point2=(x1 + dx, y, z0 - dz),
        x_resolution=10,
        y_resolution=10,
    )
    return mesh_actor(plane(), color=color, lighting=False)
