"""GPU ray cast volume rendering of a CT or MRI scan, with 3D Slicer's presets.

CT voxels are in Hounsfield units, so a preset made for one CT works on any
other: no threshold to compute, as explained in
https://discourse.vtk.org/t/how-show-the-bone-of-a-serial-dicom-files/4802.
Shifting the transfer functions fine-tunes what shows up (Slicer's "Shift").
MRI intensities have no such unit, so the MR presets usually need a shift.
"""

from itertools import pairwise

import numpy as np
import vtkmodules.vtkRenderingVolumeOpenGL2  # noqa: F401  (GPU mapper override)
from vtkmodules.util import numpy_support
from vtkmodules.vtkCommonCore import VTK_DOUBLE, VTK_FLOAT
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import (
    vtkColorTransferFunction,
    vtkVolume,
    vtkVolumeProperty,
)
from vtkmodules.vtkRenderingVolume import vtkGPUVolumeRayCastMapper

from .core import set_camera

# From Slicer's Modules/Loadable/VolumeRendering/Resources/presets.xml:
# opacity is (x, opacity) points and color (x, r, g, b) points, x in HU for CT
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
    "MR-Default": dict(
        opacity=(
            (0, 0),
            (20, 0),
            (40, 0.15),
            (120, 0.3),
            (220, 0.375),
            (1024, 0.5),
        ),
        color=(
            (0, 0, 0, 0),
            (20, 0.168627, 0, 0),
            (40, 0.403922, 0.145098, 0.0784314),
            (120, 0.780392, 0.607843, 0.380392),
            (220, 0.847059, 0.835294, 0.788235),
            (1024, 1, 1, 1),
        ),
        ambient=0.2,
        diffuse=1.0,
        specular=0.0,
        specular_power=1,
    ),
    "MR-Angio": dict(
        opacity=(
            (-2048, 0),
            (151.354, 0),
            (158.279, 0.4375),
            (190.112, 0.580357),
            (200.873, 0.732143),
            (3661, 0.741071),
        ),
        color=(
            (-2048, 0, 0, 0),
            (151.354, 0, 0, 0),
            (158.279, 0.74902, 0.376471, 0),
            (190.112, 1, 0.866667, 0.733333),
            (200.873, 0.937255, 0.937255, 0.937255),
            (3661, 1, 1, 1),
        ),
        ambient=0.2,
        diffuse=1.0,
        specular=0.0,
        specular_power=1,
    ),
    "MR-T2-Brain": dict(
        opacity=(
            (0, 0),
            (36.05, 0),
            (218.302, 0.171429),
            (412.406, 1),
            (641, 1),
        ),
        color=(
            (0, 0, 0, 0),
            (98.7223, 0.956863, 0.839216, 0.192157),
            (412.406, 0, 0.592157, 0.807843),
            (641, 1, 1, 1),
        ),
        ambient=0.3,
        diffuse=0.6,
        specular=0.5,
        specular_power=40,
    ),
}
DEFAULT_PRESET = "CT-Chest-Contrast-Enhanced"
DEFAULT_MR_PRESET = "MR-Default"


def opacity_start(preset):
    """Value where the opacity of ``preset`` starts to rise: where tissue shows up."""
    points = PRESETS[preset]["opacity"]
    for (x, _), (_, alpha) in pairwise(points):
        if alpha > 0:
            return x
    return points[0][0]


def tissue_range(image):
    """Robust (low, high) scalar range of ``image``.

    The 1st and 99.9th percentiles, ignoring the voxels at the minimum
    value: background or padding outside the scanner field of view (-3024 HU
    on CT), which would otherwise stretch the range.
    """
    values = numpy_support.vtk_to_numpy(image.point_data.GetScalars()).ravel()
    values = values[:: max(1, values.size // 1_000_000)]  # a sample is enough
    foreground = values[values > values.min()]
    if foreground.size == 0:
        return float(values.min()), float(values.max())
    low, high = np.percentile(foreground, (1, 99.9))
    return float(low), float(high)


def _nice_step(span):
    """A power of ten giving about 500 to 5000 slider steps over ``span``."""
    return 10.0 ** np.floor(np.log10(span / 500)) if span > 0 else 1.0


class VolumeRendering:
    """A ``vtkVolume`` of ``image`` whose preset, shift and shading can be changed live."""

    def __init__(self, image, preset=DEFAULT_PRESET, shift=0.0):
        self.image = image
        self.data_range = list(image.point_data.GetScalars().GetRange())
        self.tissue_range = tissue_range(image)
        self.integer = image.point_data.GetScalars().GetDataType() not in (
            VTK_FLOAT,
            VTK_DOUBLE,
        )
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
        """Offset, in scalar units (Hounsfield units for CT), of every transfer function point."""
        return self._shift

    @shift.setter
    def shift(self, value):
        self._shift = value
        self._apply()

    @property
    def shift_range(self):
        """(min, max, step) of the shift for the current preset.

        Wide enough to move where the preset's opacity starts anywhere over
        the tissue range of the volume, and always including 0.
        """
        start = opacity_start(self._preset)
        low, high = self.tissue_range
        step = _nice_step(high - low)
        if self.integer:
            step = max(step, 1.0)
        lo = min(0.0, np.floor((low - start) / step) * step)
        hi = max(0.0, np.ceil((high - start) / step) * step)
        return float(lo), float(hi), float(step)

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
    """Add a volume rendering of the CT or MRI ``image``, seen from the front. Returns the VolumeRendering."""
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
