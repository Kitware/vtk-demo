"""Color presets for ``vtkLookupTable``: ParaView's presets, or matplotlib colormaps.

``presets.json`` holds the continuous color maps of ParaView 6.2 (the ones
defined by ``RGBPoints``), in ParaView's preset format. ParaView is BSD-3-Clause
licensed, Copyright (c) Kitware, Inc.; see each preset's ``Creator``,
``Source`` and ``License`` for its origin.

    from vtk_demo.lut import lookup_table

    lut = lookup_table("Fast", value_range=(0, 10))
    mapper.lookup_table = lut
    lut.SetRange(2, 5)  # colors follow, with mapper.use_lookup_table_scalar_range

A name that is not a ParaView preset is looked up in matplotlib's colormaps,
so ``"viridis"`` (matplotlib) and ``"Viridis"`` (ParaView) both work.
"""

import json
from functools import cache
from importlib.resources import files

from vtkmodules.vtkCommonCore import vtkLookupTable
from vtkmodules.vtkRenderingCore import vtkColorTransferFunction

__all__ = ["apply_preset", "get_preset", "list_presets", "lookup_table"]

# ParaView "ColorSpace" -> vtkColorTransferFunction method
_COLOR_SPACES = {
    "RGB": "SetColorSpaceToRGB",
    "HSV": "SetColorSpaceToHSV",
    "Lab": "SetColorSpaceToLab",
    "CIELAB": "SetColorSpaceToLab",
    "Lab/CIEDE2000": "SetColorSpaceToLabCIEDE2000",
    "Diverging": "SetColorSpaceToDiverging",
    "Step": "SetColorSpaceToStep",
}


@cache
def _presets():
    text = files(__package__).joinpath("presets.json").read_text()
    return {preset["Name"]: preset for preset in json.loads(text)}


def list_presets():
    """Names of the ParaView presets."""
    return list(_presets())


def get_preset(name):
    """The ParaView preset ``name``, as a dict in ParaView's JSON format."""
    try:
        return _presets()[name]
    except KeyError:
        raise KeyError(f"No ParaView preset named {name!r}") from None


def _paraview_colors(preset, n_colors):
    """``n_colors`` RGB colors sampled evenly across ``preset``'s points."""
    ctf = vtkColorTransferFunction()
    getattr(ctf, _COLOR_SPACES.get(preset.get("ColorSpace"), "SetColorSpaceToRGB"))()
    points = preset["RGBPoints"]
    for i in range(0, len(points), 4):
        ctf.AddRGBPoint(*points[i : i + 4])
    low, high = points[0], points[-4]
    return [
        ctf.GetColor(low + (high - low) * i / (n_colors - 1)) for i in range(n_colors)
    ]


def _matplotlib_colors(name, n_colors):
    from matplotlib import colormaps

    try:
        cmap = colormaps[name]
    except KeyError:
        raise KeyError(
            f"{name!r} is neither a ParaView preset nor a matplotlib colormap"
        ) from None
    return [cmap(i / (n_colors - 1))[:3] for i in range(n_colors)]


def apply_preset(lut, name, n_colors=256, reverse=False):
    """Fill ``lut`` with the colors of ``name``; its range is left untouched.

    ``name`` is a ParaView preset (see :func:`list_presets`), or else a
    matplotlib colormap.
    """
    if name in _presets():
        preset = _presets()[name]
        colors = _paraview_colors(preset, n_colors)
        if "NanColor" in preset:
            lut.SetNanColor(*preset["NanColor"], 1)
    else:
        colors = _matplotlib_colors(name, n_colors)
    if reverse:
        colors.reverse()

    lut.SetNumberOfTableValues(n_colors)
    for i, rgb in enumerate(colors):
        lut.SetTableValue(i, *rgb, 1)
    lut.Build()
    return lut


def lookup_table(name="Fast", value_range=None, n_colors=256, reverse=False):
    """A new ``vtkLookupTable`` with the colors of ``name`` over ``value_range``."""
    lut = vtkLookupTable()
    if value_range is not None:
        lut.SetRange(*value_range)
    return apply_preset(lut, name, n_colors, reverse)
