"""Small building blocks shared by the scenes: shapes and textures.

Each shape is a plain VTK source, with the same geometry as its PyVista
counterpart (``pv.Cube``, ``pv.Cylinder``…). They are all returned as a
``vtkPolyData``, centered on the origin unless asked otherwise.
"""

import numpy as np
from vtkmodules.vtkCommonComputationalGeometry import (
    vtkParametricSpline,
    vtkParametricSuperEllipsoid,
)
from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPolyData
from vtkmodules.vtkFiltersCore import vtkCleanPolyData, vtkTubeFilter
from vtkmodules.vtkFiltersModeling import vtkLinearSubdivisionFilter
from vtkmodules.vtkFiltersSources import (
    vtkArrowSource,
    vtkConeSource,
    vtkCubeSource,
    vtkCylinderSource,
    vtkParametricFunctionSource,
    vtkPlatonicSolidSource,
)
from vtkmodules.vtkRenderingCore import vtkTexture

from .core import compute_normals, transformed, vtk_array, vtk_points


def cube(center=(0, 0, 0)):
    """Unit cube with its 8 corners shared, so its point normals are smoothed."""
    corners = (vtkCubeSource(center=center) >> vtkCleanPolyData()).update().output
    # Drop the normals of the first face around each corner: vtkPolyDataNormals
    # keeps existing ones
    corners.point_data.RemoveArray("Normals")
    return compute_normals(corners)


def cylinder(center=(0, 0, 0), radius=0.5, height=1.0, resolution=100):
    """Capped cylinder along z."""
    source = vtkCylinderSource(radius=radius, height=height, resolution=resolution)
    return transformed(source(), rotate=(90, 0, 0), translate=center)


def cone(center=(0, 0, 0), height=1.0, radius=0.5, resolution=6):
    """Capped cone pointing to +z."""
    return vtkConeSource(
        center=center,
        direction=(0, 0, 1),
        height=height,
        radius=radius,
        resolution=resolution,
    )()


def arrow(start=(0, 0, 0), tip_resolution=20, shaft_resolution=20):
    """Unit arrow pointing to +x from ``start``, with PyVista's proportions."""
    source = vtkArrowSource(
        tip_length=0.25,
        tip_radius=0.1,
        tip_resolution=tip_resolution,
        shaft_radius=0.05,
        shaft_resolution=shaft_resolution,
    )
    return transformed(source(), translate=start)


def icosphere(radius=1.0, n_subdivisions=3):
    """Sphere made of an icosahedron subdivided ``n_subdivisions`` times."""
    icosahedron = vtkPlatonicSolidSource()
    icosahedron.SetSolidTypeToIcosahedron()
    subdivide = vtkLinearSubdivisionFilter(number_of_subdivisions=n_subdivisions)
    mesh = (icosahedron >> subdivide).update().output
    points = np.asarray(mesh.points.data)
    points = radius * points / np.linalg.norm(points, axis=1, keepdims=True)
    return vtkPolyData(points=vtk_points(points), polys=mesh.polys)


def super_ellipsoid(radius=1.0, n1=1.0, n2=1.0, resolution=100):
    """Super ellipsoid of the given squareness ``n1`` and ``n2``, with point normals."""
    function = vtkParametricSuperEllipsoid(
        x_radius=radius, y_radius=radius, z_radius=radius, n1=n1, n2=n2
    )
    return vtkParametricFunctionSource(
        parametric_function=function,
        u_resolution=resolution,
        v_resolution=resolution,
        w_resolution=resolution,
    )()


def trefoil(scale=1.0, radius=0.1, n_sides=48):
    """Tube along a trefoil knot, with point normals."""
    t = np.linspace(0, 2 * np.pi, 600)
    points = (
        scale
        * np.c_[
            np.sin(t) + 2 * np.sin(2 * t), np.cos(t) - 2 * np.cos(2 * t), -np.sin(3 * t)
        ]
    )
    spline = vtkParametricSpline(points=vtk_points(points))
    curve = vtkParametricFunctionSource(parametric_function=spline, u_resolution=1199)
    tube = curve >> vtkTubeFilter(radius=radius, number_of_sides=n_sides, capping=True)
    return compute_normals(tube.update().output)


def stone_tiles_texture(n_tiles=12, size=1024, seed=0):
    """Dark stone tiles with a slight tone variation and light grout lines.

    The texture is mipmapped and flagged as sRGB, as required for a PBR base color.
    """
    rng = np.random.default_rng(seed)
    tile = size // n_tiles
    tones = rng.uniform(0.75, 1.0, (n_tiles, n_tiles))
    image = np.kron(tones, np.ones((tile, tile)))[..., None] * [52, 50, 56]
    image += rng.normal(0, 3, image.shape)  # grain
    grout = (np.arange(n_tiles * tile) % tile) < 3
    image[grout, :] = image[:, grout] = [120, 116, 110]
    return image_texture(np.clip(image, 0, 255).astype(np.uint8), srgb=True)


def image_texture(image, srgb=False):
    """Mipmapped ``vtkTexture`` of a (height, width, channels) uint8 image, top row first."""
    height, width, channels = image.shape
    data = vtkImageData(dimensions=(width, height, 1))
    # VTK images start from the bottom row
    data.point_data.SetScalars(vtk_array(image[::-1].reshape(-1, channels), "Image"))
    texture = vtkTexture(mipmap=True, use_srgb_color_space=srgb)
    texture.SetInputData(data)
    return texture
