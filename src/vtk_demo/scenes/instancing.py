"""Draw many copies of one mesh, with every strategy VTK offers.

An :class:`InstanceLayer` describes the copies once: where they go, how they
are scaled, oriented and colored. The same layer can then be drawn

- with GPU instancing: :func:`glyph_actor`, one actor and a ``vtkGlyph3DMapper``;
- naively: :func:`instance_actors`, one actor per copy, all sharing one mapper;
- baked: :func:`bake_layer`, every copy merged into a single polydata, ready to
  go into a composite dataset (see :mod:`vtk_demo.scenes.composite`).

All three produce the very same picture, which makes them easy to compare.
"""

from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

import numpy as np
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkRenderingCore import vtkActor, vtkGlyph3DMapper, vtkPolyDataMapper

from .core import (
    cell_array,
    compute_normals,
    make_property,
    rgb,
    triangles,
    triangulate,
    vtk_array,
    vtk_points,
)


@dataclass
class InstanceLayer:
    """One copy of ``source`` (a ``vtkPolyData``) at each of ``points``.

    ``scale`` is a (n,) array to scale uniformly or (n, 3) to scale per axis,
    ``orient`` a (n, 3) array of directions the source's +x axis turns to and
    ``colors`` a (n, 3) array of RGB colors in [0, 255]. Without ``colors``,
    every copy gets ``color``. ``props`` are extra actor property values
    (``specular``, ``opacity``…, see :func:`~vtk_demo.scenes.core.make_property`),
    applied by the strategies that create actors.
    """

    name: str
    points: Any
    source: vtkPolyData
    scale: Any = None
    orient: Any = None
    colors: Any = None
    color: Any = "white"
    props: dict = field(default_factory=dict)

    def __len__(self):
        return len(self.points)

    @cached_property
    def mesh(self):
        """The source, triangulated."""
        return triangulate(self.source)

    @property
    def n_triangles(self):
        return len(self) * self.mesh.number_of_cells

    def _actor_props(self):
        props = {"interpolation": "phong", **self.props}
        if self.colors is None:
            props.setdefault("color", self.color)
        return props


# GPU instancing -------------------------------------------------------------


def glyph_actor(layer):
    """A single actor drawing every copy of ``layer`` with a ``vtkGlyph3DMapper``.

    VTK.wasm does not carry the mapper's array selection over, so the scale
    and orientation arrays are also made the active scalars and vectors,
    which the mapper uses by default.
    """
    cloud = vtkPolyData(points=vtk_points(np.asarray(layer.points, dtype=np.float32)))
    mapper = vtkGlyph3DMapper()
    mapper.SetInputData(cloud)
    mapper.SetSourceData(layer.mesh)

    if layer.scale is None:
        mapper.SetScaleModeToNoDataScaling()
    else:
        scale = np.asarray(layer.scale, dtype=np.float32)
        cloud.point_data.SetScalars(vtk_array(scale, "scale"))
        mapper.SetScaleArray("scale")
        if scale.ndim == 2:
            mapper.SetScaleModeToScaleByVectorComponents()
        else:
            mapper.SetScaleModeToScaleByMagnitude()

    if layer.orient is None:
        mapper.orient = False
    else:
        orient = np.asarray(layer.orient, dtype=np.float32)
        cloud.point_data.SetVectors(vtk_array(orient, "orient"))
        mapper.SetOrientationArray("orient")
        mapper.SetOrientationModeToDirection()

    if layer.colors is None:
        mapper.scalar_visibility = False
    else:
        colors = np.clip(layer.colors, 0, 255).astype(np.uint8)
        cloud.point_data.AddArray(vtk_array(colors, "rgb"))
        mapper.SetScalarModeToUsePointFieldData()
        mapper.SelectColorArray("rgb")
        mapper.SetColorModeToDirectScalars()
        mapper.scalar_visibility = True

    return vtkActor(mapper=mapper, property=make_property(**layer._actor_props()))


def add_glyph_layer(renderer, layer):
    """Add :func:`glyph_actor` to ``renderer``; return (instances, triangles)."""
    renderer.AddActor(glyph_actor(layer))
    return len(layer), layer.n_triangles


# One actor per copy ---------------------------------------------------------


def instance_actors(layer):
    """One ``vtkActor`` per copy, all sharing one mapper on the source.

    Copies without a per copy color share one property too.
    """
    mapper = vtkPolyDataMapper(scalar_visibility=False)
    mapper.SetInputData(layer.mesh)

    props = layer._actor_props()
    shared = make_property(**props) if layer.colors is None else None
    colors = None if shared is not None else np.clip(layer.colors, 0, 255) / 255
    scale, orient = layer.scale, layer.orient

    actors = []
    for i, position in enumerate(layer.points):
        if shared is None:
            prop = make_property(**{**props, "color": colors[i]})
        else:
            prop = shared
        actor = vtkActor(mapper=mapper, property=prop, position=position)
        if scale is not None:
            actor.scale = scale[i] if np.ndim(scale) == 2 else (scale[i],) * 3
        if orient is not None:
            # Same rotation as vtkGlyph3DMapper: 180 degrees around the
            # bisector of +x and the target direction
            d = orient[i] / np.linalg.norm(orient[i])
            actor.RotateWXYZ(180, d[0] + 1, d[1], d[2])
        actors.append(actor)
    return actors


def add_actor_layer(renderer, layer):
    """Add :func:`instance_actors` to ``renderer``; return (actors, triangles)."""
    for actor in instance_actors(layer):
        renderer.AddActor(actor)
    return len(layer), layer.n_triangles


# Baked copies ---------------------------------------------------------------


class InstanceArrays:
    """Every copy of ``layer`` transformed on the CPU, one row per copy.

    ``points``, ``normals`` and ``colors`` are (n, m, 3) arrays (``normals`` is
    None when the source has none and ``normals=False``), and ``faces`` the
    (c, 3) triangles of one copy. Rows can be sliced and regrouped freely
    with :func:`merge_instances`.
    """

    def __init__(self, layer, normals=False):
        points = np.asarray(layer.points, dtype=float)
        n = len(points)
        source = layer.mesh
        if normals and "Normals" not in source.point_data:
            source = compute_normals(source, split=True)
        p = np.asarray(source.points.data, dtype=float)

        # Same transform as the actors: position + rotation @ (scale * point)
        s = np.ones((n, 3)) if layer.scale is None else np.asarray(layer.scale, float)
        s = s if s.ndim == 2 else np.repeat(s[:, None], 3, axis=1)
        xyz = s[:, None, :] * p[None]
        nrm = None
        if "Normals" in source.point_data:
            # Normals take the inverse scale; rotations keep their length
            nrm = np.asarray(source.point_data["Normals"], dtype=float)
            nrm = nrm[None] / s[:, None, :]
        if layer.orient is not None:
            # Same rotation as vtkGlyph3DMapper: 180 degrees around the bisector
            # of +x and the target direction, which is 2 a a^T - I
            orient = np.asarray(layer.orient, dtype=float)
            d = orient / np.linalg.norm(orient, axis=1, keepdims=True)
            a = d + [1, 0, 0]
            a /= np.linalg.norm(a, axis=1, keepdims=True)
            rotation = 2 * a[:, :, None] * a[:, None, :] - np.eye(3)
            xyz = np.einsum("nij,nmj->nmi", rotation, xyz)
            if nrm is not None:
                nrm = np.einsum("nij,nmj->nmi", rotation, nrm)
        xyz += points[:, None, :]
        if nrm is not None:
            nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)

        colors = (
            np.tile(rgb(layer.color), (n, 1)) if layer.colors is None else layer.colors
        )
        colors = np.clip(colors, 0, 255).astype(np.uint8)

        self.points = xyz.astype(np.float32)
        self.normals = None if nrm is None else nrm.astype(np.float32)
        self.colors = np.repeat(colors[:, None, :], len(p), axis=1)
        self.faces = triangles(source)

    def __len__(self):
        return len(self.points)


def merge_instances(pieces, keep_alive=None):
    """Merge ``(InstanceArrays, first, last)`` row ranges into one ``vtkPolyData``.

    The result carries the "Normals" (when every piece has some) and "rgb"
    point arrays.

    Up to VTK 9.7.20260913, dropping the Python wrapper of an object VTK still
    holds costs time proportional to the number of such drops so far (fixed
    upstream by VTK commit d1489916). Pass a list as ``keep_alive`` to collect
    the wrappers instead of dropping them when building many meshes.
    """
    points, normals, colors, faces = [], [], [], []
    offset = 0
    for arrays, first, last in pieces:
        n, m = last - first, arrays.points.shape[1]
        points.append(arrays.points[first:last].reshape(-1, 3))
        if arrays.normals is not None:
            normals.append(arrays.normals[first:last].reshape(-1, 3))
        colors.append(arrays.colors[first:last].reshape(-1, 3))
        faces.append(
            (arrays.faces[None] + offset + (np.arange(n) * m)[:, None, None]).ravel()
        )
        offset += n * m

    # Every wrapper is created here, rather than by VTK's numpy helpers, so
    # that they can all be kept alive
    xyz = vtk_array(np.concatenate(points))
    vtk_xyz = vtkPoints(data=xyz)
    connectivity = np.concatenate(faces).astype(np.int64)
    offsets = vtk_array(np.arange(0, len(connectivity) + 1, 3))
    connectivity = vtk_array(connectivity)
    cells = cell_array(offsets, connectivity)
    mesh = vtkPolyData(points=vtk_xyz, polys=cells)
    point_data = mesh.GetPointData()
    wrappers = [mesh, xyz, vtk_xyz, offsets, connectivity, cells, point_data]
    if len(normals) == len(pieces):
        vtk_normals = vtk_array(np.concatenate(normals), "Normals")
        point_data.SetNormals(vtk_normals)
        wrappers.append(vtk_normals)
    vtk_colors = vtk_array(np.concatenate(colors), "rgb")
    point_data.AddArray(vtk_colors)
    wrappers.append(vtk_colors)

    if keep_alive is not None:
        keep_alive.extend(wrappers)
    return mesh


def bake_layer(layer, normals=False):
    """Merge every copy of ``layer`` into a single ``vtkPolyData``.

    Colors are stored in the "rgb" point array. Normals are carried over from
    the source when it has some, or computed when ``normals`` is true.
    """
    arrays = InstanceArrays(layer, normals=normals)
    return merge_instances([(arrays, 0, len(arrays))])
