"""Live simulation: a damped 2D wave equation rendered as a moving surface."""

import numpy as np
from vtkmodules.vtkCommonDataModel import vtkPolyData
from vtkmodules.vtkFiltersSources import vtkPlaneSource

from .core import mesh_actor, set_background, set_camera, triangulate


class Wave:
    """Damped 2D wave equation on a ``n`` x ``n`` grid, with random raindrops."""

    def __init__(self, n, seed=0):
        self.n = n
        self.u = np.zeros((n, n), dtype=np.float32)
        self.u_prev = np.zeros_like(self.u)
        self.rng = np.random.default_rng(seed)
        x = np.arange(-6, 7, dtype=np.float32)
        self.drop = np.exp(-(x[:, None] ** 2 + x[None, :] ** 2) / 8)

    def raindrop(self):
        i, j = self.rng.integers(10, self.n - 10, 2)
        h = self.drop.shape[0] // 2
        self.u[i - h : i + h + 1, j - h : j + h + 1] += (
            self.rng.uniform(0.5, 1.5) * self.drop
        )

    def step(self):
        u, prev = self.u, self.u_prev
        lap = np.zeros_like(u)
        lap[1:-1, 1:-1] = (
            u[:-2, 1:-1] + u[2:, 1:-1] + u[1:-1, :-2] + u[1:-1, 2:] - 4 * u[1:-1, 1:-1]
        )
        nxt = (2 * u - prev + 0.25 * lap) * 0.998
        self.u_prev, self.u = u, nxt


class WaveSurface:
    """A :class:`Wave` bound to a triangulated plane whose height follows it.

    Each :meth:`advance` only modifies the points and the "height" scalars of
    :attr:`mesh`, which is what makes streaming it to a client cheap.
    """

    def __init__(self, resolution=512, amplitude=0.08, rain_every=15, seed=0):
        n = resolution
        self.wave = Wave(n, seed)
        self.amplitude = amplitude
        self.rain_every = rain_every
        self.steps = 0

        # The unit square, as triangles with no point data
        plane = vtkPlaneSource(
            center=(0.5, 0.5, 0), x_resolution=n - 1, y_resolution=n - 1
        )
        grid = triangulate(plane())
        self.mesh = vtkPolyData(points=grid.points, polys=grid.polys)
        self.mesh.point_data["height"] = self.wave.u.ravel().copy()

        # The arrays updated in place: VTK arrays, indexed like numpy ones
        self._points = self.mesh.points.data
        self._height = self.mesh.point_data["height"]

    def advance(self):
        if self.steps % self.rain_every == 0:
            self.wave.raindrop()
        self.wave.step()
        self.steps += 1

        height = self.wave.u.ravel()
        self._points[:, 2] = self.amplitude * height
        self._height[:] = height
        self._points.Modified()
        self._height.Modified()
        self.mesh.Modified()


def build_wave_scene(renderer, resolution=512, **kwargs):
    """Add a :class:`WaveSurface` on a dark background. Returns the surface."""
    surface = WaveSurface(resolution, **kwargs)
    set_background(renderer, "#0f1115")
    renderer.AddActor(
        mesh_actor(
            surface.mesh,
            scalars="height",
            cmap="RdBu_r",
            clim=(-0.3, 0.3),
            specular=0.5,
            interpolation="flat",
        )
    )
    set_camera(renderer, (0.5, -0.9, 0.8), (0.5, 0.5, 0), (0, 0, 1))
    return surface
