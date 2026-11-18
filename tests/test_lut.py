import pytest
from vtkmodules.vtkCommonCore import vtkLookupTable

from vtk_demo import lut


def rgb(table, i):
    # vtkLookupTable stores 8 bit colors
    return pytest.approx(table.GetTableValue(i)[:3], abs=1 / 255)


def test_presets():
    names = lut.list_presets()
    assert len(names) > 100
    for name in ("Fast", "Cool to Warm", "Viridis", "Turbo", "Jet"):
        assert name in names
    for name in names:
        preset = lut.get_preset(name)
        assert len(preset["RGBPoints"]) % 4 == 0, name
        table = lut.lookup_table(name, n_colors=16)  # every color space builds
        assert table.GetNumberOfTableValues() == 16, name


def test_paraview_preset():
    table = lut.lookup_table("Fast", value_range=(2, 5))
    assert table.GetRange() == (2, 5)
    assert table.GetNumberOfTableValues() == 256
    assert rgb(table, 0) == (0.0564, 0.0564, 0.47)
    assert rgb(table, 255) == (0.59, 0.0767, 0.119475)
    assert table.GetNanColor()[:3] == (0, 1, 0)


def test_preset_range_is_normalized():
    # Jet's points span [-1, 1]: the table still covers all of them
    points = lut.get_preset("Jet")["RGBPoints"]
    table = lut.lookup_table("Jet", n_colors=8)
    assert rgb(table, 0) == points[1:4]
    assert rgb(table, 7) == points[-3:]


def test_matplotlib_fallback():
    table = lut.lookup_table("viridis", n_colors=4)
    assert rgb(table, 0) == (0.267004, 0.004874, 0.329415)
    reversed_table = lut.lookup_table("viridis", n_colors=4, reverse=True)
    assert rgb(reversed_table, 3) == (0.267004, 0.004874, 0.329415)


def test_apply_preset_keeps_range():
    table = vtkLookupTable()
    table.SetRange(-1, 3)
    lut.apply_preset(table, "Cool to Warm", n_colors=32)
    assert table.GetRange() == (-1, 3)
    assert table.GetNumberOfTableValues() == 32


def test_unknown_name():
    with pytest.raises(KeyError, match="neither"):
        lut.lookup_table("not a color map")
    with pytest.raises(KeyError):
        lut.get_preset("viridis")
