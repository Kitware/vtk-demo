"""Transparency stress test.

An opaque gold knot trapped inside nested translucent shells, circled by a
ring of overlapping tinted glass cubes, with soap bubbles drifting above a
see-through floor. Almost every actor is translucent and many of them
overlap, which exercises depth peeling and how each backend sorts and blends
translucent geometry.
"""

import colorsys

import numpy as np
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkFiltersCore import (
    vtkContourFilter,
    vtkExtractEdges,
    vtkWindowedSincPolyDataFilter,
)
from vtkmodules.vtkFiltersSources import vtkPlaneSource, vtkSphereSource

from .core import compute_normals, mesh_actor, set_background, set_camera, transformed
from .primitives import cube, cylinder, trefoil

# (iso value, color, opacity) of the nested shells, innermost first
SHELLS = [
    (1.15, "#ff6f61", 0.35),
    (1.65, "#ffd166", 0.25),
    (2.15, "#06d6a0", 0.18),
    (2.65, "#118ab2", 0.12),
]


def wobbly_shells(shells=SHELLS, n=120, extent=3.2):
    """Iso-surfaces of a radial field with a wobble, so the shells are not spheres.

    Yields ``(surface, color, opacity)`` for each ``(iso value, color, opacity)``.
    """
    spacing = 2 * extent / (n - 1)
    grid = vtkImageData(
        dimensions=(n, n, n), spacing=(spacing,) * 3, origin=(-extent,) * 3
    )
    axis = -extent + spacing * np.arange(n)
    z, y, x = (a.ravel() for a in np.meshgrid(axis, axis, axis, indexing="ij"))
    r = np.sqrt(x**2 + y**2 + z**2)
    theta = np.arctan2(y, x)
    phi = np.arccos(np.clip(z / np.maximum(r, 1e-9), -1, 1))
    grid.point_data["f"] = r * (1 + 0.1 * np.sin(4 * theta) * np.sin(3 * phi))
    grid.point_data.SetActiveScalars("f")
    for value, color, opacity in shells:
        contour = vtkContourFilter(compute_normals=False)
        contour.SetValue(0, value)
        smooth = vtkWindowedSincPolyDataFilter(number_of_iterations=30)  # Taubin
        yield compute_normals(smooth(contour(grid))), color, opacity


def build_transparency_scene(renderer, n_peels=10):
    """Lay out the scene around the origin with z up.

    Returns ``(n_translucent_actors, n_actors)``.
    """
    actors = []

    def add(mesh, **props):
        props.setdefault("interpolation", "phong")
        props.setdefault("specular", 0.8)
        props.setdefault("specular_power", 60)
        actors.append(mesh_actor(mesh, **props))
        renderer.AddActor(actors[-1])

    # Opaque core, so there is something solid to see through the shells
    add(
        transformed(trefoil(0.28, 0.12), translate=(0, 0, 3.2)),
        color="#ffc356",
        specular=1.0,
    )

    # Nested translucent shells, centered on the knot
    for surface, color, opacity in wobbly_shells():
        add(transformed(surface, translate=(0, 0, 3.2)), color=color, opacity=opacity)

    # Ring of overlapping glass cubes, hue sweeping around it
    n_cubes = 16
    for i in range(n_cubes):
        a = 2 * np.pi * i / n_cubes
        add(
            transformed(
                cube(),
                scale=1.4,
                rotate=(30, 0, np.degrees(a) + 20),
                translate=(5.2 * np.cos(a), 5.2 * np.sin(a), 1.2),
            ),
            color=colorsys.hsv_to_rgb(i / n_cubes, 0.7, 1.0),
            opacity=0.4,
            interpolation="flat",
            edge_visibility=True,
            edge_color="white",
            line_width=1,
        )

    # Soap bubbles floating above everything
    rng = np.random.default_rng(7)
    for _ in range(40):
        radius = rng.uniform(0.15, 0.55)
        a, d = rng.uniform(0, 2 * np.pi), rng.uniform(0, 7)
        center = (d * np.cos(a), d * np.sin(a), rng.uniform(4.5, 8.5))
        hue = colorsys.hsv_to_rgb(rng.uniform(0.45, 0.85), 0.35, 1.0)
        bubble = vtkSphereSource(
            radius=radius, center=center, theta_resolution=48, phi_resolution=48
        )
        add(bubble(), color=hue, opacity=0.2, specular=1.0, specular_power=100)

    # Translucent floor with a grid drawn on it
    floor = vtkPlaneSource(
        origin=(-9, -9, 0),
        point1=(9, -9, 0),
        point2=(-9, 9, 0),
        x_resolution=18,
        y_resolution=18,
    )()
    add(floor, color="#9ad1ff", opacity=0.25, interpolation="flat")
    add(vtkExtractEdges()(floor), color="#9ad1ff", opacity=0.5)

    # Opaque pillars under the floor, visible through it
    for i in range(6):
        a = 2 * np.pi * (i + 0.5) / 6
        center = (3 * np.cos(a), 3 * np.sin(a), -1.5)
        add(cylinder(center, radius=0.35, height=3, resolution=64), color="#ef476f")

    set_background(renderer, "#0b1d33", top="#3a6ea5")
    renderer.SetUseDepthPeeling(True)
    renderer.SetMaximumNumberOfPeels(n_peels)
    renderer.SetOcclusionRatio(0.0)
    set_camera(renderer, (14, -11, 10), (0, 0, 2.5), (0, 0, 1), view_angle=35)

    n_translucent = sum(actor.property.opacity < 1 for actor in actors)
    return n_translucent, len(actors)
