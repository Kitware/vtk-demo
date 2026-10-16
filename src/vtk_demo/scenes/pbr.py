"""Physically based rendering showcase.

A gold Lucy statue on a marble pedestal, surrounded by a ring of material
spheres (metals and plastics, smooth to rough), clear-coated and brushed
knots, all lit by image based lighting from a skybox.

PBR shaders are only available in VTK's OpenGL / WebGL backend for now: VTK's
WebGPU backend shades this scene with plain Phong, without environment
reflections nor base color textures.
"""

import numpy as np
from vtkmodules.vtkFiltersSources import vtkDiskSource, vtkSphereSource
from vtkmodules.vtkFiltersTexture import vtkTextureMapToPlane
from vtkmodules.vtkRenderingCore import vtkSkybox

from . import datasets
from .core import compute_normals, mesh_actor, set_camera, transformed, triangulate
from .primitives import cylinder, stone_tiles_texture, super_ellipsoid, trefoil

# (color, metallic) of the sphere ring; roughness sweeps around it
MATERIALS = [
    ("#ffc356", 1.0),  # gold
    ("#f9d0c0", 1.0),  # copper
    ("#fafaf9", 1.0),  # silver
    ("#d0d3d4", 1.0),  # aluminium
    ("#c4c7c7", 1.0),  # iron
    ("#c1bab1", 1.0),  # titanium
    ("#c0392b", 0.0),  # red plastic
    ("#2e86c1", 0.0),  # blue plastic
    ("#27ae60", 0.0),  # green plastic
    ("#f4f6f7", 0.0),  # white ceramic
    ("#1c1c1c", 0.0),  # black rubber
    ("#f39c12", 0.0),  # orange plastic
]


def add_pbr_mesh(renderer, mesh, y_up=False, **props):
    """Add ``mesh`` with a PBR property, smooth shaded. Returns the actor.

    ``props`` are property values (``color``, ``metallic``, ``roughness``,
    ``coat_strength``, ``anisotropy``, ``base_color_texture``…), see
    :func:`~vtk_demo.scenes.core.make_property`. With ``y_up``, a z up
    ``mesh`` is turned y up.
    """
    if "Normals" not in mesh.point_data:
        mesh = compute_normals(mesh)
    if y_up:
        mesh = transformed(mesh, rotate=(-90, 0, 0))
    actor = mesh_actor(mesh, interpolation="pbr", **props)
    renderer.AddActor(actor)
    return actor


def build_pbr_scene(renderer):
    """Lay the scene out with z up, then turn it y up to match the skybox.

    Downloads Lucy and the skybox on first use. Returns the number of triangles.
    """
    n_triangles = 0

    def add(mesh, **props):
        nonlocal n_triangles
        n_triangles += mesh.number_of_cells
        return add_pbr_mesh(renderer, mesh, y_up=True, **props)

    # Tiled floor and clear-coated marble pedestal
    disk = vtkDiskSource(
        inner_radius=0,
        outer_radius=7,
        radial_resolution=1,
        circumferential_resolution=256,
    )
    floor = vtkTextureMapToPlane(automatic_plane_generation=True)(triangulate(disk()))
    add(floor, base_color_texture=stone_tiles_texture(), metallic=0.0, roughness=0.3)
    add(
        cylinder(center=(0, 0, 0.201), radius=0.9, height=0.4, resolution=128),
        color="#ece8e1",
        metallic=0.0,
        roughness=0.45,
        coat_strength=1.0,
        coat_roughness=0.05,
    )

    # Lucy in gold, normalized to stand 2.4 units tall on the pedestal
    lucy = datasets.lucy()
    xyz = np.asarray(lucy.points.data)
    low, high = xyz.min(axis=0), xyz.max(axis=0)
    xyz[:] = (xyz - (low + high) / 2) * (2.4 / (high[2] - low[2])) + (0, 0, 1.6)
    lucy.points.data.Modified()
    add(compute_normals(lucy), color="#ffc356", metallic=1.0, roughness=0.22)

    # Ring of material spheres: metals then plastics, each from mirror to matte
    n = len(MATERIALS)
    for i, (color, metallic) in enumerate(MATERIALS):
        angle = 2 * np.pi * i / n
        sphere = vtkSphereSource(
            radius=0.45,
            center=(3.4 * np.cos(angle), 3.4 * np.sin(angle), 0.45),
            theta_resolution=96,
            phi_resolution=96,
        )
        add(
            sphere(),
            color=color,
            metallic=metallic,
            roughness=0.05 + 0.9 * (i % (n // 2)) / (n // 2 - 1),
        )

    # Floating knots: mirror chrome, clear-coated car paint, brushed copper
    for angle, props in [
        (90, {"color": "#e8e8e8", "metallic": 1.0, "roughness": 0.02}),
        (
            210,
            {
                "color": "#8e0e1b",
                "metallic": 0.2,
                "roughness": 0.55,
                "coat_strength": 1.0,
                "coat_roughness": 0.02,
            },
        ),
        (
            330,
            {"color": "#d98c5f", "metallic": 1.0, "roughness": 0.35, "anisotropy": 0.8},
        ),
    ]:
        a = np.radians(angle)
        center = (1.9 * np.cos(a), 1.9 * np.sin(a), 2.1)
        add(
            transformed(trefoil(0.22, 0.09), rotate=(25, 0, 0), translate=center),
            **props,
        )

    # Outer ring of ceramic pillars, each balancing a polished rounded cube
    for i, color in enumerate(["#fafaf9", "#ffc356", "#f9d0c0", "#c1bab1"] * 2):
        a = 2 * np.pi * (i + 0.5) / 8
        x, y = 5.4 * np.cos(a), 5.4 * np.sin(a)
        add(
            cylinder(center=(x, y, 0.601), radius=0.28, height=1.2, resolution=96),
            color="#1f2a44",
            metallic=0.0,
            roughness=0.25,
            coat_strength=1.0,
            coat_roughness=0.0,
        )
        cube = transformed(
            super_ellipsoid(radius=0.3, n1=0.3, n2=0.3),
            rotate=(45, 35.26, np.degrees(a)),
            translate=(x, y, 1.2 + 0.3 * np.sqrt(3)),
        )
        add(compute_normals(cube), color=color, metallic=1.0, roughness=0.1)

    # Image based lighting from the skybox, also drawn as the background
    cubemap = datasets.sky_box()
    renderer.UseImageBasedLightingOn()
    renderer.UseSphericalHarmonicsOff()  # not for cube maps
    renderer.SetEnvironmentTexture(cubemap, True)  # sRGB
    renderer.AddActor(vtkSkybox(texture=cubemap))
    set_camera(renderer, (10.5, 5.5, 11.5), (0, 1.0, 0), (0, 1, 0), view_angle=35)

    return n_triangles
