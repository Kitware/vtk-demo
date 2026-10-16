"""Reusable scene builders, in plain VTK and numpy, with no UI dependency.

Every ``build_*`` function takes a ``vtkRenderer``, fills it (actors,
background, camera…) and returns a few statistics about what it added. Lower
level helpers (:mod:`.instancing`, :mod:`.composite`, :mod:`.core`) return
VTK objects too: ``vtkActor``, ``vtkPolyData``, ``vtkProperty``…

    from vtkmodules.vtkRenderingCore import vtkRenderer, vtkRenderWindow
    from vtk_demo.scenes import build_glyph_island

    renderer = vtkRenderer()
    build_glyph_island(renderer)
    window = vtkRenderWindow(size=(1280, 800))
    window.AddRenderer(renderer)
    window.Render()

To fill a PyVista plotter instead, see :mod:`vtk_demo.pyvista_adapter`.
"""

from .benchmark import build_sphere_actors, build_sphere_mesh
from .bunny import build_bunny_scene
from .composite import composite_actor, partitioned_collection, scattered_collection
from .core import make_property, mesh_actor, rgb
from .galaxy import build_galaxy_scene, galaxy_cloud, galaxy_points
from .instancing import (
    InstanceArrays,
    InstanceLayer,
    add_actor_layer,
    add_glyph_layer,
    bake_layer,
    glyph_actor,
    instance_actors,
    merge_instances,
)
from .island import (
    build_actor_island,
    build_archipelago,
    build_glyph_island,
    build_partitioned_island,
    island_layers,
    island_offsets,
)
from .isosurface import Isosurface, build_isosurface_scene
from .pbr import add_pbr_mesh, build_pbr_scene
from .primitives import stone_tiles_texture, trefoil
from .transparency import build_transparency_scene, wobbly_shells
from .wave import Wave, WaveSurface, build_wave_scene

__all__ = [
    "InstanceArrays",
    "InstanceLayer",
    "Isosurface",
    "Wave",
    "WaveSurface",
    "add_actor_layer",
    "add_glyph_layer",
    "add_pbr_mesh",
    "bake_layer",
    "build_actor_island",
    "build_archipelago",
    "build_bunny_scene",
    "build_galaxy_scene",
    "build_glyph_island",
    "build_isosurface_scene",
    "build_partitioned_island",
    "build_pbr_scene",
    "build_sphere_actors",
    "build_sphere_mesh",
    "build_transparency_scene",
    "build_wave_scene",
    "composite_actor",
    "galaxy_cloud",
    "galaxy_points",
    "glyph_actor",
    "instance_actors",
    "island_layers",
    "island_offsets",
    "make_property",
    "merge_instances",
    "mesh_actor",
    "partitioned_collection",
    "rgb",
    "scattered_collection",
    "stone_tiles_texture",
    "trefoil",
    "wobbly_shells",
]
