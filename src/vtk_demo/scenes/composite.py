"""Composite datasets: many meshes drawn by a single actor.

A ``vtkPartitionedDataSetCollection`` rendered by a ``vtkCompositePolyDataMapper``
lets one actor draw any number of blocks. These helpers build such collections
out of :class:`~vtk_demo.scenes.instancing.InstanceLayer` objects, either one
partition per layer (:func:`scattered_collection`) or cut into an arbitrary
number of partitions (:func:`partitioned_collection`).
"""

import numpy as np
from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkPartitionedDataSet,
    vtkPartitionedDataSetCollection,
    vtkPolyData,
)
from vtkmodules.vtkRenderingCore import vtkActor, vtkCompositePolyDataMapper

from .core import make_property, vtk_points
from .instancing import InstanceArrays, bake_layer, merge_instances


def composite_actor(dataset, color_array="rgb", **props):
    """One actor drawing ``dataset`` with a ``vtkCompositePolyDataMapper``.

    Every block is colored directly by its ``color_array`` RGB point array.
    ``props`` are actor property values, see
    :func:`~vtk_demo.scenes.core.make_property`.
    """
    mapper = vtkCompositePolyDataMapper(scalar_visibility=True)
    mapper.SetInputDataObject(dataset)
    mapper.SetScalarModeToUsePointFieldData()
    mapper.SelectColorArray(color_array)
    mapper.SetColorModeToDirectScalars()
    props.setdefault("interpolation", "phong")
    return vtkActor(mapper=mapper, property=make_property(**props))


def scattered_collection(layers, offsets, name="copy"):
    """One partitioned dataset per offset, one partition per layer.

    Offsets are (n, 2) or (n, 3); copies are named ``f"{name} {i}"``.

    Each layer is baked once; the copies are shallow, so they share their
    cells and colors and only differ by their (translated) points.
    """
    meshes = {layer.name: bake_layer(layer) for layer in layers}
    collection = vtkPartitionedDataSetCollection()
    for i, offset in enumerate(np.asarray(offsets, dtype=np.float32)):
        delta = np.zeros(3, dtype=np.float32)
        delta[: len(offset)] = offset
        copy = vtkPartitionedDataSet()
        for j, (name, mesh) in enumerate(meshes.items()):
            partition = vtkPolyData()
            partition.ShallowCopy(mesh)
            # New points, the shared ones stay untouched
            partition.points = vtk_points(np.asarray(mesh.points.data) + delta)
            copy.SetPartition(j, partition)
            copy.GetMetaData(j).Set(vtkCompositeDataSet.NAME(), name)
        collection.SetPartitionedDataSet(i, copy)
        collection.GetMetaData(i).Set(vtkCompositeDataSet.NAME(), f"{name} {i}")
    return collection


def partitioned_collection(layers, n_partitions, name="dataset", keep_alive=None):
    """Every copy of every layer, split into ``n_partitions`` partitions.

    Copies are listed layer after layer and cut into consecutive groups of
    (nearly) equal count, each group baked into one partition. With 1 partition
    everything is one polydata; with one per copy, every copy is its own block.
    Every partition carries normals and colors, so the vertex data is the same
    whatever the partition count.

    Returns ``(collection, n_partitions)``, the count clamped to the copy count.
    See :func:`~vtk_demo.scenes.instancing.merge_instances` for ``keep_alive``.
    """
    arrays = [InstanceArrays(layer, normals=True) for layer in layers]
    n_meshes = sum(len(a) for a in arrays)
    n_partitions = max(1, min(n_partitions, n_meshes))

    # Global copy index where each layer starts, and where each partition starts
    starts = np.cumsum([0, *(len(a) for a in arrays)])
    bounds = np.linspace(0, n_meshes, n_partitions + 1).round().astype(int)

    dataset = vtkPartitionedDataSet()
    for i in range(n_partitions):
        lo, hi = bounds[i], bounds[i + 1]
        pieces = []
        for a, start, end in zip(arrays, starts[:-1], starts[1:], strict=True):
            first, last = max(lo, start), min(hi, end)
            if first < last:
                pieces.append((a, first - start, last - start))
        dataset.SetPartition(i, merge_instances(pieces, keep_alive=keep_alive))

    collection = vtkPartitionedDataSetCollection()
    collection.SetPartitionedDataSet(0, dataset)
    collection.GetMetaData(0).Set(vtkCompositeDataSet.NAME(), name)
    return collection, n_partitions
