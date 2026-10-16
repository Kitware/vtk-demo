"""Interactive isosurface of a CT scan, extracted with vtkFlyingEdges3D."""

from vtkmodules.vtkFiltersCore import vtkFlyingEdges3D

from . import datasets
from .core import mesh_actor, set_camera

BONE = "#e3dac9"


class Isosurface:
    """A single contour of ``volume`` whose iso value can be changed live."""

    def __init__(self, volume, value=None):
        self.volume = volume
        self.data_range = list(volume.point_data.GetScalars().GetRange())
        self.filter = vtkFlyingEdges3D(number_of_contours=1, compute_scalars=False)
        self.filter.SetInputDataObject(volume)
        self.value = 0.5 * sum(self.data_range) if value is None else value

    @property
    def value(self):
        return self.filter.GetValue(0)

    @value.setter
    def value(self, value):
        self.filter.SetValue(0, value)
        self.filter.Update()

    @property
    def n_triangles(self):
        return self.filter.GetOutput().GetNumberOfCells()


def build_isosurface_scene(renderer, volume=None, value=None):
    """Add a bone colored contour of ``volume`` (default: a CT head). Returns the Isosurface."""
    if volume is None:
        volume = datasets.head()
    iso = Isosurface(volume, value)
    # Flying edges already computes normals
    renderer.AddActor(mesh_actor(iso.filter, color=BONE, interpolation="gouraud"))
    set_camera(
        renderer,
        (-404.8, 472.4, 92.0),
        (126.7, 124.0, 92.5),
        (0.208, -0.178, -0.962),
    )
    renderer.ResetCamera(volume.bounds)
    return iso
