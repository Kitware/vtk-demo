import numpy as np
import pytest
import pyvista as pv

from vtk_demo import scenes
from vtk_demo.pyvista_adapter import add_scene


@pytest.fixture
def plotter():
    pl = pv.Plotter(off_screen=True, window_size=(320, 240))
    yield pl
    pl.close()


def test_scene_camera_survives_first_render(plotter):
    add_scene(plotter, scenes.build_glyph_island)
    position = plotter.camera.position
    plotter.render()
    assert plotter.renderer.GetActors().GetNumberOfItems() == 5
    np.testing.assert_allclose(plotter.camera.position, position)
    np.testing.assert_allclose(position, (36, -32, 20))


def test_screenshot(plotter):
    add_scene(plotter, scenes.build_transparency_scene)
    image = plotter.screenshot()
    assert image.shape == (240, 320, 3)
    assert image.std() > 0
