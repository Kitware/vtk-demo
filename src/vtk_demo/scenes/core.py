"""VTK and numpy helpers shared by the scenes: arrays, meshes, actors and views.

Everything here is plain VTK, through its Python friendly API: keyword
constructors, snake_case properties, numpy backed arrays and ``>>`` pipelines.

Two PyVista quirks to keep in mind, as the scenes also run in PyVista apps:

- the renderer a scene is built into may be a PyVista one, whose subclasses
  of ``vtkRenderer`` and ``vtkCamera`` reject VTK's snake_case API: the
  scenes call their VTK methods (``SetBackground()``…) instead;
- importing PyVista removes VTK's Python overrides of the classes it
  subclasses, which takes away ``vtkCellArray(offsets=..., connectivity=...)``
  among others: :func:`cell_array` works either way.
"""

import numpy as np
from matplotlib import colormaps
from matplotlib.colors import to_rgb
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkDataArray, vtkLookupTable, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData
from vtkmodules.vtkCommonExecutionModel import vtkAlgorithm
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersCore import vtkPolyDataNormals, vtkTriangleFilter
from vtkmodules.vtkFiltersGeneral import vtkTransformFilter
from vtkmodules.vtkRenderingCore import (
    VTK_FLAT,
    VTK_GOURAUD,
    VTK_PBR,
    VTK_PHONG,
    vtkActor,
    vtkPolyDataMapper,
    vtkProperty,
)

# Colors ---------------------------------------------------------------------


def color(value):
    """Any matplotlib color (name, hex, RGB in [0, 1]) as an RGB float tuple."""
    return to_rgb(value)


def rgb(value):
    """Any matplotlib color as a float array in [0, 255]."""
    return np.round(255 * np.array(color(value)))


def lookup_table(cmap, clim, n_colors=256):
    """``vtkLookupTable`` sampling the matplotlib colormap ``cmap`` over ``clim``."""
    table = vtkLookupTable(number_of_table_values=n_colors, table_range=clim)
    for i, value in enumerate(colormaps[cmap](np.linspace(0, 1, n_colors))):
        table.SetTableValue(i, *value)
    return table


# Arrays and meshes ----------------------------------------------------------


def vtk_array(array, name=None):
    """A VTK data array sharing the memory of a contiguous numpy ``array``."""
    result = numpy_to_vtk(np.ascontiguousarray(array))
    if name is not None:
        result.SetName(name)
    return result


def vtk_points(array):
    """``vtkPoints`` holding a (n, 3) array, with its dtype (float32 stays float32)."""
    return vtkPoints(data=vtk_array(array))


def cell_array(offsets, connectivity):
    """``vtkCellArray`` from its ``offsets`` and ``connectivity``, numpy or VTK arrays."""
    arrays = [
        a if isinstance(a, vtkDataArray) else vtk_array(np.asarray(a, dtype=np.int64))
        for a in (offsets, connectivity)
    ]
    cells = vtkCellArray()
    cells.SetData(*arrays)
    return cells


def triangles(mesh):
    """The (n, 3) point ids of the triangles of a triangulated ``mesh``."""
    return np.asarray(mesh.polys.connectivity_array).reshape(-1, 3)


def point_cloud(points):
    """``vtkPolyData`` with one vertex cell per point of a (n, 3) array."""
    n = len(points)
    verts = cell_array(np.arange(n + 1), np.arange(n))
    return vtkPolyData(points=vtk_points(points), verts=verts)


def triangulate(mesh):
    """``mesh`` with its polygons cut into triangles, without vertices nor lines."""
    return vtkTriangleFilter(pass_verts=False, pass_lines=False)(mesh)


def compute_normals(mesh, split=False):
    """``mesh`` with point normals, duplicating points along sharp edges if ``split``."""
    return vtkPolyDataNormals(splitting=split, compute_cell_normals=False)(mesh)


def transformed(mesh, scale=1, rotate=(0, 0, 0), translate=(0, 0, 0)):
    """``mesh`` scaled, rotated around x, then y, then z (degrees), then translated."""
    transform = vtkTransform()
    transform.PostMultiply()
    transform.Scale(np.broadcast_to(scale, 3))
    transform.RotateX(rotate[0])
    transform.RotateY(rotate[1])
    transform.RotateZ(rotate[2])
    transform.Translate(translate)
    return vtkTransformFilter(transform=transform)(mesh)


# Actors ---------------------------------------------------------------------

INTERPOLATION = {
    "flat": VTK_FLAT,
    "gouraud": VTK_GOURAUD,
    "phong": VTK_PHONG,
    "pbr": VTK_PBR,
}


def make_property(**props):
    """A ``vtkProperty`` from snake_case values: ``make_property(color="gold", specular=0.5)``.

    Colors take anything :func:`color` does and ``interpolation`` a name
    ("flat", "gouraud", "phong" or "pbr"). ``specular_power`` defaults to 100
    for a tight highlight: VTK's default of 1 spreads it over the whole surface.
    """
    props.setdefault("specular_power", 100)
    for key in ("color", "edge_color"):
        if key in props:
            props[key] = color(props[key])
    if isinstance(props.get("interpolation"), str):
        props["interpolation"] = INTERPOLATION[props["interpolation"]]
    return vtkProperty(**props)


def mesh_actor(mesh, scalars=None, cmap="viridis", clim=None, **props):
    """A ``vtkActor`` drawing ``mesh``, a ``vtkPolyData`` or the output of an algorithm.

    Without ``scalars`` the mesh takes the property color (see
    :func:`make_property` for ``props``). Otherwise it is colored by its
    ``scalars`` point array, through the matplotlib colormap ``cmap`` over
    ``clim`` (default: the array range).
    """
    mapper = vtkPolyDataMapper()
    if isinstance(mesh, vtkAlgorithm):
        mapper.input_connection = mesh.output_port
    else:
        mapper.SetInputData(mesh)

    if scalars is None:
        mapper.scalar_visibility = False
    else:
        if clim is None:
            clim = mesh.point_data[scalars].GetRange()
        mapper.SetScalarModeToUsePointFieldData()
        mapper.SelectColorArray(scalars)
        mapper.lookup_table = lookup_table(cmap, clim)
        mapper.scalar_range = clim
        mapper.interpolate_scalars_before_mapping = True
    return vtkActor(mapper=mapper, property=make_property(**props))


def n_actors(renderer):
    """Number of actors in ``renderer``."""
    return renderer.GetActors().GetNumberOfItems()


# Views ----------------------------------------------------------------------


def set_background(renderer, bottom, top=None):
    """A plain ``bottom`` color, or a gradient from ``bottom`` to ``top``."""
    renderer.SetBackground(color(bottom))
    renderer.SetGradientBackground(top is not None)
    if top is not None:
        renderer.SetBackground2(color(top))


def set_camera(renderer, position, focal_point, view_up, view_angle=None):
    """Place the active camera of ``renderer``; call once every actor is in."""
    camera = renderer.GetActiveCamera()
    camera.SetPosition(position)
    camera.SetFocalPoint(focal_point)
    camera.SetViewUp(view_up)
    if view_angle is not None:
        camera.SetViewAngle(view_angle)
    renderer.ResetCameraClippingRange()


def look_from(renderer, direction, view_up, azimuth=0, elevation=0):
    """Look at every actor from ``direction``, then orbit the camera around them."""
    bounds = np.reshape(renderer.ComputeVisiblePropBounds(), (3, 2))
    center = bounds.mean(axis=1)
    set_camera(renderer, center + direction, center, view_up)
    renderer.ResetCamera()
    camera = renderer.GetActiveCamera()
    camera.Azimuth(azimuth)
    camera.Elevation(elevation)
    renderer.ResetCamera()
