import subprocess
import sys

import numpy as np
import pytest
from vtkmodules.vtkRenderingCore import vtkRenderer

from vtk_demo import scenes
from vtk_demo.scenes.core import n_actors
from vtk_demo.scenes.instancing import InstanceLayer
from vtk_demo.scenes.primitives import arrow


@pytest.fixture
def renderer():
    return vtkRenderer()


@pytest.fixture
def layer():
    rng = np.random.default_rng(0)
    n = 20
    return InstanceLayer(
        "arrows",
        rng.uniform(-5, 5, (n, 3)),
        arrow(start=(-0.5, 0, 0)),
        scale=rng.uniform(0.5, 2, n),
        orient=rng.normal(size=(n, 3)),
        colors=rng.uniform(0, 255, (n, 3)),
    )


def test_scenes_do_not_need_pyvista():
    code = (
        "import sys\n"
        "from vtkmodules.vtkRenderingCore import vtkRenderer\n"
        "from vtk_demo import scenes\n"
        "scenes.build_partitioned_island(vtkRenderer(), 10)\n"
        "assert 'pyvista' not in sys.modules\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_instancing_strategies_agree(layer):
    """Baked copies match one actor per copy exactly, and fit in the glyph bounds."""
    baked = scenes.bake_layer(layer)
    assert baked.GetNumberOfCells() == layer.n_triangles
    assert "rgb" in baked.point_data

    source = np.c_[
        np.asarray(layer.mesh.points.data), np.ones(len(layer.mesh.points.data))
    ]
    rows = np.asarray(baked.points.data).reshape(len(layer), -1, 3)
    actors = scenes.instance_actors(layer)
    assert len(actors) == len(layer)
    for actor, row in zip(actors, rows, strict=True):
        m = actor.GetMatrix()
        matrix = np.array([[m.GetElement(i, j) for j in range(4)] for i in range(4)])
        np.testing.assert_allclose(row, (source @ matrix.T)[:, :3], atol=1e-4)

    glyph_bounds = np.array(scenes.glyph_actor(layer).GetBounds())
    assert np.all(np.array(baked.GetBounds())[::2] >= glyph_bounds[::2] - 1e-4)
    assert np.all(np.array(baked.GetBounds())[1::2] <= glyph_bounds[1::2] + 1e-4)


def test_instancing_layers(renderer, layer):
    scenes.add_glyph_layer(renderer, layer)
    scenes.add_actor_layer(renderer, layer)
    assert n_actors(renderer) == 1 + len(layer)


def test_partitions_keep_triangles(layer):
    total = []
    for n in (1, 7, 1000):
        collection, count = scenes.partitioned_collection([layer, layer], n)
        assert count == min(n, 2 * len(layer))
        total.append(
            sum(
                collection.GetPartition(0, i).GetNumberOfCells()
                for i in range(collection.GetNumberOfPartitions(0))
            )
        )
    assert total == [2 * layer.n_triangles] * 3


def test_island_layers():
    layers = scenes.island_layers()
    assert [layer.name for layer in layers] == [
        "terrain columns",
        "tree trunks",
        "tree crowns",
        "wind arrows",
        "cloud puffs",
    ]
    assert sum(len(layer) for layer in layers) == 43_132


def test_glyph_island(renderer):
    n_actors, n_instances, n_triangles = scenes.build_glyph_island(renderer)
    assert n_actors == 5
    assert n_instances == 43_132
    assert n_triangles == 1_105_088


def test_archipelago(renderer):
    n_partitions, n_triangles = scenes.build_archipelago(renderer, 2)
    assert n_partitions == 10
    assert n_triangles == 2 * sum(x.n_triangles for x in scenes.island_layers())


def test_partitioned_island(renderer):
    n_partitions, n_meshes, _ = scenes.build_partitioned_island(renderer, 50)
    assert (n_partitions, n_meshes) == (50, 43_132)


def test_transparency(renderer):
    n_translucent, n_actors = scenes.build_transparency_scene(renderer)
    assert 0 < n_translucent < n_actors
    assert renderer.GetUseDepthPeeling()


def test_galaxy(renderer):
    cloud = scenes.build_galaxy_scene(renderer, 10_000)
    assert cloud.GetNumberOfPoints() == cloud.GetNumberOfCells() == 10_000
    assert np.asarray(cloud.point_data["radius"]).dtype == np.float32


def test_wave(renderer):
    surface = scenes.build_wave_scene(renderer, 64)
    points = surface.mesh.GetPoints()
    mtime = points.GetMTime()
    for _ in range(20):
        surface.advance()
    assert surface.steps == 20
    assert points.GetMTime() > mtime
    assert np.abs(np.asarray(points.data)[:, 2]).max() > 0


def test_benchmark(renderer):
    assert scenes.build_sphere_actors(renderer, 9) > 0
    assert n_actors(renderer) == 9
