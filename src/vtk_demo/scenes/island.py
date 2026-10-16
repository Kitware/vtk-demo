"""A voxel island: tens of thousands of objects, drawn four different ways.

The island is a terrain of box columns covered in a forest, swept by a
swirling wind drawn with arrows and topped with puffy clouds: 43,132 objects
described by five :class:`~vtk_demo.scenes.instancing.InstanceLayer`.
The same layers feed four scenes that only differ by how VTK draws them:

- :func:`build_glyph_island`: one ``vtkGlyph3DMapper`` actor per layer (GPU instancing);
- :func:`build_actor_island`: one actor per object;
- :func:`build_archipelago`: copies of the island in a single composite actor;
- :func:`build_partitioned_island`: the island cut into N composite partitions.
"""

import numpy as np
from matplotlib import colormaps

from .composite import composite_actor, partitioned_collection, scattered_collection
from .core import n_actors, rgb, set_background, set_camera
from .instancing import InstanceLayer, add_actor_layer, add_glyph_layer
from .primitives import arrow, cone, cube, cylinder, icosphere

GRID = 200  # terrain columns per side
CELL = 0.2  # terrain column width
WATER = 0.6  # sea level
REACH = 25  # radius of an island, clouds included

# (max height, color) of the terrain bands, from the sea floor up
BANDS = [
    (WATER, "#2d7dd2"),  # water
    (0.95, "#e9d8a6"),  # sand
    (2.6, "#5a9e3d"),  # grass
    (4.0, "#7d6e63"),  # rock
    (np.inf, "#f4f6f7"),  # snow
]


def terrain(rng, grid=GRID, cell=CELL):
    """Height field of a few gaussian hills with ripples, quantized into steps.

    Returns the flat (x, y, height) arrays of the ``grid`` x ``grid`` columns.
    """
    x = (np.arange(grid) - (grid - 1) / 2) * cell
    x, y = np.meshgrid(x, x, indexing="ij")
    h = np.zeros_like(x)
    for amplitude, spread, width in [(6.5, 3, 3.5), *[(2.5, 11, 3.5)] * 8]:
        cx, cy = rng.uniform(-spread, spread, 2)
        h += (
            rng.uniform(0.6, 1.0)
            * amplitude
            * np.exp(
                -((x - cx) ** 2 + (y - cy) ** 2)
                / (2 * rng.uniform(0.6, 1.0) ** 2 * width**2)
            )
        )
    h += 0.35 * np.sin(0.7 * x) * np.cos(0.6 * y)
    h *= np.clip(1.3 - np.hypot(x, y) / 18, 0, 1)  # sink the borders: an island
    h = np.maximum(np.round(h / cell) * cell, WATER)
    return x.ravel(), y.ravel(), h.ravel()


def island_layers(seed=3):
    """The island around the origin with z up, as five instance layers."""
    rng = np.random.default_rng(seed)
    layers = []

    # Voxel terrain: one unit box standing on z=0, stretched per column
    x, y, h = terrain(rng)
    colors = np.empty((h.size, 3))
    lower = -np.inf
    for upper, color in BANDS:
        band = (h > lower) & (h <= upper)
        colors[band] = rgb(color)
        lower = upper
    colors *= rng.uniform(0.9, 1.05, (h.size, 1))  # per column tone variation
    layers.append(
        InstanceLayer(
            "terrain columns",
            np.c_[x, y, np.zeros_like(h)],
            cube(center=(0, 0, 0.5)),
            scale=np.c_[np.full_like(h, CELL), np.full_like(h, CELL), h],
            colors=colors,
            props={"specular": 0.2},
        )
    )

    # Forest on the grass: trunks and crowns share the same tree positions
    grass = (h > BANDS[1][0]) & (h <= BANDS[2][0])
    trees = np.flatnonzero(grass & (rng.random(h.size) < 0.12))
    tree_points = np.c_[x[trees], y[trees], h[trees]]
    tree_points[:, :2] += rng.uniform(-0.3, 0.3, (trees.size, 2)) * CELL
    tree_scale = rng.uniform(0.35, 0.7, trees.size)
    layers.append(
        InstanceLayer(
            "tree trunks",
            tree_points,
            cylinder(center=(0, 0, 0.2), radius=0.05, height=0.4),
            scale=tree_scale,
            color="#6b4423",
        )
    )
    green = rgb("#2f7d32") * rng.uniform(0.6, 1.2, (trees.size, 1))
    green[:, 0] += rng.uniform(0, 60, trees.size)  # a few autumn trees
    layers.append(
        InstanceLayer(
            "tree crowns",
            tree_points,
            cone(center=(0, 0, 0.75), height=0.9, radius=0.28, resolution=12),
            scale=tree_scale,
            colors=green,
            props={"specular": 0.1},
        )
    )

    # Wind field: arrows on stacked layers, swirling around the island
    s = np.linspace(-15, 15, 22)
    wx, wy, wz = (a.ravel() for a in np.meshgrid(s, s, [9.0, 11.0], indexing="ij"))
    r = np.hypot(wx, wy) + 1e-6
    swirl = np.exp(-((r - 9) ** 2) / 60)
    wind = np.c_[
        -wy / r * swirl + 0.25,
        wx / r * swirl,
        0.15 * np.sin(wx / 3) * np.cos(wy / 3),
    ]
    speed = np.linalg.norm(wind, axis=1)
    layers.append(
        InstanceLayer(
            "wind arrows",
            np.c_[wx, wy, wz],
            arrow(start=(-0.5, 0, 0), tip_resolution=16, shaft_resolution=16),
            scale=0.4 + 0.9 * speed / speed.max(),
            orient=wind,
            colors=255 * colormaps["plasma"](speed / speed.max())[:, :3],
            props={"specular": 0.5},
        )
    )

    # Clouds: flattened clusters of spheres drifting high above
    puffs = []
    for _ in range(18):
        a, d = rng.uniform(0, 2 * np.pi), rng.uniform(6, 22)
        center = (d * np.cos(a), d * np.sin(a), rng.uniform(15, 18))
        n = rng.integers(25, 60)
        puffs.append(center + rng.normal(0, 1, (n, 3)) * [1.3, 0.8, 0.25])
    puffs = np.concatenate(puffs)
    layers.append(
        InstanceLayer(
            "cloud puffs",
            puffs,
            icosphere(radius=1, n_subdivisions=2),
            scale=rng.uniform(0.3, 0.65, len(puffs)),
            colors=np.repeat(rng.uniform(225, 255, (len(puffs), 1)), 3, axis=1),
            props={"specular": 0.1},
        )
    )

    return layers


def island_offsets(n, spacing=60, seed=7):
    """Random X and Y offsets at least ``spacing`` apart, centered on the origin."""
    rng = np.random.default_rng(seed)
    radius = 0.6 * spacing * np.sqrt(n)
    offsets = [np.zeros(2)]
    while len(offsets) < n:
        for _ in range(1000):
            candidate = rng.uniform(-radius, radius, 2)
            if all(np.linalg.norm(candidate - o) >= spacing for o in offsets):
                offsets.append(candidate)
                break
        else:
            radius *= 1.2  # crowded: spread out
    offsets = np.array(offsets)
    return offsets - offsets.mean(axis=0)


def set_island_view(renderer, zoom=1.0):
    """Sky gradient and the default camera, backed off by ``zoom``."""
    set_background(renderer, "#cfe8ff", top="#4a90d9")
    set_camera(
        renderer,
        (36 * zoom, -32 * zoom, 5 + 15 * zoom),
        (0, 0, 5),
        (0, 0, 1),
        view_angle=35,
    )


def build_glyph_island(renderer, seed=3):
    """One ``vtkGlyph3DMapper`` actor per layer.

    Returns ``(n_actors, n_instances, n_triangles)``.
    """
    n_instances = n_triangles = 0
    for layer in island_layers(seed):
        n, t = add_glyph_layer(renderer, layer)
        n_instances += n
        n_triangles += t
    set_island_view(renderer)
    return n_actors(renderer), n_instances, n_triangles


def build_actor_island(renderer, seed=3):
    """One actor per object, actors of the same kind sharing one mapper.

    Returns ``(n_actors, n_triangles)``.
    """
    n_triangles = 0
    for layer in island_layers(seed):
        n_triangles += add_actor_layer(renderer, layer)[1]
    set_island_view(renderer)
    return n_actors(renderer), n_triangles


# A single actor, so a single property: the specular is a compromise
# between the per layer values of the glyph and actor scenes
COMPOSITE_SPECULAR = 0.2


def build_archipelago(renderer, n_islands=4, seed=3):
    """Copies of the island scattered in one composite dataset and one actor.

    Each island is a partitioned dataset with one partition per layer.
    Returns ``(n_partitions, n_triangles)``.
    """
    layers = island_layers(seed)
    offsets = island_offsets(n_islands)
    collection = scattered_collection(layers, offsets, name="island")
    renderer.AddActor(composite_actor(collection, specular=COMPOSITE_SPECULAR))

    # The default view, backed off to take in the whole archipelago
    set_island_view(renderer, 1 + 1.3 * np.linalg.norm(offsets, axis=1).max() / REACH)
    n_triangles = n_islands * sum(layer.n_triangles for layer in layers)
    return n_islands * len(layers), n_triangles


def build_partitioned_island(renderer, n_partitions=100, seed=3, keep_alive=None):
    """The island in one composite actor, cut into ``n_partitions`` partitions.

    Returns ``(n_partitions, n_meshes, n_triangles)``, ``n_partitions`` being
    clamped to the object count. See
    :func:`~vtk_demo.scenes.instancing.merge_instances` for ``keep_alive``.
    """
    layers = island_layers(seed)
    collection, n_partitions = partitioned_collection(
        layers, n_partitions, name="island", keep_alive=keep_alive
    )
    renderer.AddActor(composite_actor(collection, specular=COMPOSITE_SPECULAR))
    set_island_view(renderer)
    n_meshes = sum(len(layer) for layer in layers)
    return n_partitions, n_meshes, sum(layer.n_triangles for layer in layers)
