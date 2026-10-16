"""Synthetic benchmark scenes.

- :func:`build_sphere_mesh`: a single sphere with ~N triangles (raw throughput);
- :func:`build_sphere_actors`: N small spheres, each its own actor and mapper
  (per actor overhead).
"""

import colorsys
import math

from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

from .core import look_from, mesh_actor, set_background

BACKGROUND = (0.1, 0.11, 0.13)


def sphere_resolution(n_triangles):
    """Resolution giving a vtkSphereSource of about ``n_triangles`` triangles."""
    # vtkSphereSource yields 2 * r * (r - 1) triangles for theta = phi = r
    return max(8, round(0.5 + math.sqrt(n_triangles / 2)))


def view_isometric(renderer):
    set_background(renderer, BACKGROUND)
    look_from(renderer, (1, 1, 1), (0, 0, 1))


def build_sphere_mesh(renderer, n_triangles):
    """One sphere of about ``n_triangles`` triangles. Returns its triangle count."""
    r = sphere_resolution(n_triangles)
    sphere = vtkSphereSource(theta_resolution=r, phi_resolution=r)()
    # The sphere already carries point normals
    actor = mesh_actor(sphere, color=(0.85, 0.55, 0.3), interpolation="gouraud")
    renderer.AddActor(actor)
    view_isometric(renderer)
    return sphere.number_of_cells


def build_sphere_actors(renderer, n_actors, resolution=12, spacing=1.5):
    """A grid of ``n_actors`` spheres, one actor and mapper each. Returns the triangle count."""
    sphere = vtkSphereSource(
        radius=0.5, theta_resolution=resolution, phi_resolution=resolution
    )()
    side = math.ceil(math.sqrt(n_actors))
    for i in range(n_actors):
        actor = vtkActor(
            mapper=vtkPolyDataMapper(input_data=sphere),
            position=((i % side) * spacing, (i // side) * spacing, 0),
        )
        actor.property.color = colorsys.hsv_to_rgb(i / max(n_actors, 1), 0.65, 0.95)
        renderer.AddActor(actor)
    view_isometric(renderer)
    return sphere.number_of_cells * n_actors
