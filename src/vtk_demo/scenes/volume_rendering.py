"""GPU ray cast volume rendering of a CT scan, with 3D Slicer's presets.

CT voxels are in Hounsfield units, so a preset made for one CT works on any
other: no threshold to compute, as explained in
https://discourse.vtk.org/t/how-show-the-bone-of-a-serial-dicom-files/4802.
Shifting the transfer functions fine-tunes what shows up (Slicer's "Shift").
"""

import numpy as np
import vtkmodules.vtkRenderingVolumeOpenGL2  # noqa: F401  (GPU mapper override)
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import (
    vtkColorTransferFunction,
    vtkVolume,
    vtkVolumeProperty,
)
from vtkmodules.vtkRenderingVolume import vtkGPUVolumeRayCastMapper

from .core import set_camera

# From Slicer's Modules/Loadable/VolumeRendering/Resources/presets.xml:
# opacity is (x, opacity) points and color (x, r, g, b) points, x in HU
PRESETS = {
    "CT-Chest-Contrast-Enhanced": dict(
        opacity=(
            (-3024, 0),
            (67.0106, 0),
            (251.105, 0.446429),
            (439.291, 0.625),
            (3071, 0.616071),
        ),
        color=(
            (-3024, 0, 0, 0),
            (67.0106, 0.54902, 0.25098, 0.14902),
            (251.105, 0.882353, 0.603922, 0.290196),
            (439.291, 1, 0.937033, 0.954531),
            (3071, 0.827451, 0.658824, 1),
        ),
        ambient=0.1,
        diffuse=0.9,
        specular=0.2,
        specular_power=10,
    ),
    "CT-Bone": dict(
        opacity=(
            (-3024, 0),
            (-16.4458, 0),
            (641.385, 0.715686),
            (3071, 0.705882),
        ),
        color=(
            (-3024, 0, 0, 0),
            (-16.4458, 0.729412, 0.254902, 0.301961),
            (641.385, 0.905882, 0.815686, 0.552941),
            (3071, 1, 1, 1),
        ),
        ambient=0.1,
        diffuse=0.9,
        specular=0.2,
        specular_power=10,
    ),
    "CT-Muscle": dict(
        opacity=(
            (-3024, 0),
            (-155.407, 0),
            (217.641, 0.676471),
            (419.736, 0.833333),
            (3071, 0.803922),
        ),
        color=(
            (-3024, 0, 0, 0),
            (-155.407, 0.54902, 0.25098, 0.14902),
            (217.641, 0.882353, 0.603922, 0.290196),
            (419.736, 1, 0.937033, 0.954531),
            (3071, 0.827451, 0.658824, 1),
        ),
        ambient=0.1,
        diffuse=0.9,
        specular=0.2,
        specular_power=10,
    ),
    "CT-Chest-Vessels": dict(
        opacity=(
            (-3024, 0),
            (-1278.35, 0),
            (22.8277, 0.428571),
            (439.291, 0.625),
            (3071, 0.616071),
        ),
        color=(
            (-3024, 0, 0, 0),
            (-1278.35, 0.54902, 0.25098, 0.14902),
            (22.8277, 0.882353, 0.603922, 0.290196),
            (439.291, 1, 0.937033, 0.954531),
            (3071, 0.827451, 0.658824, 1),
        ),
        ambient=0.2,
        diffuse=1.0,
        specular=0.0,
        specular_power=1,
    ),
    "CT-Cardiac3": dict(
        opacity=(
            (-3024, 0),
            (-86.9767, 0),
            (45.3791, 0.169643),
            (139.919, 0.589286),
            (347.907, 0.607143),
            (1224.16, 0.607143),
            (3071, 0.616071),
        ),
        color=(
            (-3024, 0, 0, 0),
            (-86.9767, 0, 0.25098, 1),
            (45.3791, 1, 0, 0),
            (139.919, 1, 0.894893, 0.894893),
            (347.907, 1, 1, 0.25098),
            (1224.16, 1, 1, 1),
            (3071, 0.827451, 0.658824, 1),
        ),
        ambient=0.1,
        diffuse=0.9,
        specular=0.2,
        specular_power=10,
    ),
    "CT-Lung": dict(
        opacity=(
            (-1000, 0),
            (-600, 0),
            (-599, 0.15),
            (-400, 0.15),
            (-399, 0),
            (2952, 0),
        ),
        color=(
            (-1000, 0.3, 0.3, 1),
            (-600, 0, 0, 1),
            (-530, 0.134704, 0.781726, 0.0724558),
            (-460, 0.929244, 1, 0.109473),
            (-400, 0.888889, 0.254949, 0.0240258),
            (2952, 1, 0.3, 0.3),
        ),
        ambient=0.2,
        diffuse=1.0,
        specular=0.0,
        specular_power=1,
    ),
}
DEFAULT_PRESET = "CT-Chest-Contrast-Enhanced"


class VolumeRendering:
    """A ``vtkVolume`` of ``image`` whose preset, shift and shading can be changed live."""

    def __init__(self, image, preset=DEFAULT_PRESET, shift=0.0):
        self.image = image
        self.data_range = list(image.point_data.GetScalars().GetRange())
        self.mapper = vtkGPUVolumeRayCastMapper()
        self.mapper.SetInputDataObject(image)
        self.color = vtkColorTransferFunction()
        self.opacity = vtkPiecewiseFunction()
        self.property = vtkVolumeProperty(shade=True)
        self.property.SetInterpolationTypeToLinear()
        self.property.SetColor(self.color)
        self.property.SetScalarOpacity(self.opacity)
        self.volume = vtkVolume(mapper=self.mapper, property=self.property)
        self._preset = preset
        self._shift = shift
        self._apply()

    @property
    def preset(self):
        return self._preset

    @preset.setter
    def preset(self, name):
        self._preset = name
        self._apply()

    @property
    def shift(self):
        """Offset, in Hounsfield units, of every transfer function point."""
        return self._shift

    @shift.setter
    def shift(self, value):
        self._shift = value
        self._apply()

    @property
    def shade(self):
        """Whether the volume is lit, using its gradient as normal (the preset's lighting)."""
        return bool(self.property.GetShade())

    @shade.setter
    def shade(self, value):
        self.property.SetShade(bool(value))

    def _apply(self):
        preset = PRESETS[self._preset]
        self.opacity.RemoveAllPoints()
        for x, alpha in preset["opacity"]:
            self.opacity.AddPoint(x + self._shift, alpha)
        self.color.RemoveAllPoints()
        for x, r, g, b in preset["color"]:
            self.color.AddRGBPoint(x + self._shift, r, g, b)
        self.property.SetAmbient(preset["ambient"])
        self.property.SetDiffuse(preset["diffuse"])
        self.property.SetSpecular(preset["specular"])
        self.property.SetSpecularPower(preset["specular_power"])


def build_volume_rendering_scene(renderer, image, preset=DEFAULT_PRESET):
    """Add a volume rendering of the CT ``image``, seen from the front. Returns the VolumeRendering."""
    vr = VolumeRendering(image, preset)
    renderer.AddVolume(vr.volume)
    renderer.SetBackground(0.45, 0.47, 0.75)
    renderer.SetBackground2(0.7, 0.72, 0.9)
    renderer.GradientBackgroundOn()
    # Patient (LPS) coordinates: look from the anterior side, superior up
    center = np.reshape(image.GetBounds(), (3, 2)).mean(axis=1)
    set_camera(renderer, center - (0, 1, 0), center, (0, 0, 1))
    renderer.ResetCamera(image.GetBounds())
    return vr
