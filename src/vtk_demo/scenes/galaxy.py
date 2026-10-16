"""Procedural spiral galaxy: tens of millions of points, generated with numpy."""

import numpy as np

from .core import mesh_actor, point_cloud, set_camera


def galaxy_points(n_points, arms=4, seed=0):
    """Return ``(points, radius)`` float32 arrays of a spiral galaxy with a central bulge."""
    rng = np.random.default_rng(seed)
    n_bulge = n_points // 5
    n_disk = n_points - n_bulge

    # Disk: points scattered around logarithmic spiral arms
    r = rng.exponential(0.35, n_disk).astype(np.float32) + 0.05
    arm = rng.integers(0, arms, n_disk)
    theta = np.log(r * 20) * 2.2 + arm * (2 * np.pi / arms)
    theta += rng.normal(0, 0.35, n_disk) / (1 + 2 * r)
    disk = np.empty((n_disk, 3), dtype=np.float32)
    disk[:, 0] = r * np.cos(theta)
    disk[:, 1] = r * np.sin(theta)
    disk[:, 2] = rng.normal(0, 0.03, n_disk) * np.exp(-r)

    # Bulge: dense gaussian core
    bulge = rng.normal(0, [0.12, 0.12, 0.07], (n_bulge, 3)).astype(np.float32)

    points = np.concatenate([disk, bulge])
    radius = np.linalg.norm(points, axis=1).astype(np.float32)
    return points, radius


def galaxy_cloud(n_points, arms=4, seed=0):
    """The galaxy as a ``vtkPolyData`` point cloud with a "radius" point array."""
    points, radius = galaxy_points(n_points, arms, seed)
    cloud = point_cloud(points)
    cloud.point_data["radius"] = radius
    return cloud


def build_galaxy_scene(renderer, n_points=20_000_000, arms=4, seed=0):
    """Add the galaxy as 1 pixel points colored by radius. Returns the cloud."""
    cloud = galaxy_cloud(n_points, arms, seed)
    renderer.AddActor(
        mesh_actor(
            cloud,
            scalars="radius",
            cmap="inferno_r",
            clim=(0, 1.2),
            representation=0,  # points
            point_size=1,
        )
    )
    set_camera(renderer, (0, -2.6, 1.5), (0, 0, 0), (0, 0, 1))
    return cloud
