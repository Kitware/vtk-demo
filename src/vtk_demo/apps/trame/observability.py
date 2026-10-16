"""Observability shared by the trame demos: first frame time and interaction fps.

``static/observability.js`` measures in the browser what is actually presented,
for both the local (VTK.wasm or vtk.js) and the remote (server image stream)
views, and sends each measurement back. The server prints a short summary
of each measurement on stdout::

    [obs] local · webgpu · first frame 2310 ms
    [obs] remote · image · drag 41 fps (p95 31 ms) · server render 12.4 ms

With ``--obs-verbose`` it prints the full measurement instead, as JSON, which
is also what gets appended to ``--obs-log`` when given::

    OBS {"type": "first_frame", "mode": "local", "api": "webgpu", "ms": 2310.4, ...}

The same events are also kept in the page, on ``window.__obs.summary()``.

It also selects the server rendering backend: with ``--webgpu`` the server
renders with VTK's WebGPU backend too, so that local and remote rendering use
the same API when VTK provides it. Otherwise the server falls back to OpenGL,
which the demos report when rendering remotely.
"""

import argparse
import json
import os
import time
from pathlib import Path

from trame.widgets import client

STATIC = Path(__file__).parent / "static"

# JS expression to bind on the local view's "scene loaded" event
SCENE_READY = "utils.get('__obs')?.sceneReady('local')"


def add_arguments(parser, webgpu=True):
    if webgpu:
        parser.add_argument(
            "--webgpu",
            action="store_true",
            help="Render with WebGPU, in the browser (VTK.wasm) and on the server "
            "when VTK supports it (OpenGL otherwise)",
        )
    parser.add_argument(
        "--obs-log",
        metavar="PATH",
        help="Append the measurements (JSON lines) to this file",
    )
    parser.add_argument(
        "--obs-verbose",
        action="store_true",
        help="Print the full measurements (JSON) instead of a short summary",
    )
    parser.add_argument(
        "--no-hud",
        action="store_true",
        help="Hide the fps / first frame overlay",
    )


def parse_args():
    parser = argparse.ArgumentParser(add_help=False)
    add_arguments(parser)
    return parser.parse_known_args()[0]


def select_backend():
    """Pick the rendering API from the command line, for the browser and the server.

    Must run before the plotter, and therefore its render window, is created.
    Returns ``'webgpu'`` or ``'webgl'``, the VTK.wasm rendering option.
    """
    if not parse_args().webgpu:
        return "webgl"

    os.environ["VTK_GRAPHICS_BACKEND"] = "WEBGPU"
    try:
        # Registers the WebGPU render window override, when VTK was built with it
        import vtkmodules.vtkRenderingWebGPU  # noqa: F401
    except ImportError:
        pass
    return "webgpu"


def check_server_backend(render_window, rendering=None):
    """Return the server rendering API ('WebGPU' or 'OpenGL') of ``render_window``.

    With ``--webgpu``, the server still renders with OpenGL when this VTK build
    has no vtkRenderingWebGPU module (``VTK_ENABLE_WEBGPU=OFF``).
    """
    class_name = render_window.GetClassName()
    backend = "WebGPU" if "WebGPU" in class_name else "OpenGL"
    return backend


class Observability:
    """Collect the measurements of the browser for one demo.

    ``render_window`` is the server one: the time spent in its ``Render()``
    calls is attached to remote interactions as ``server_render_call``. That is
    the CPU side of the render only; the GPU may still be busy afterwards.

    ``hud_bottom`` is the distance in pixels between the overlay and the bottom
    of the page; raise it to keep the overlay above a footer.
    """

    def __init__(
        self, server, demo, rendering, server_backend, render_window, hud_bottom=8
    ):
        args = parse_args()
        self.log = Path(args.obs_log) if args.obs_log else None
        self.verbose = args.obs_verbose
        self.base = {
            "demo": demo,
            "client_rendering": rendering,
            "server_backend": server_backend,
        }

        server.enable_module(
            {"serve": {"__obs": str(STATIC)}, "scripts": ["__obs/observability.js"]}
        )
        server.state.obs_hud = not args.no_hud
        server.state.obs_hud_bottom = hud_bottom
        server.trigger("obs_report")(self._on_report)

        # Server render times, attached to the next remote interaction report
        self._renders = []
        self._render_start = None
        render_window.AddObserver("StartEvent", self._on_render_start)
        render_window.AddObserver("EndEvent", self._on_render_end)

    def watch_mode(self, is_remote):
        """Tell the browser about the rendering mode; call within the UI layout.

        ``is_remote`` is a JS expression, true when rendering on the server.
        """
        client.ClientStateChange(
            value=is_remote,
            immediate=True,
            trigger_on_create=True,
            change=f"utils.get('__obs')?.setMode(({is_remote}) ? 'remote' : 'local')",
        )

    def hook_vtkjs(self, ref):
        """Detect when the vtk.js view of a VtkRemoteLocalView has loaded its scene.

        Call within the UI layout. ``ref`` is the ref of the VtkRemoteLocalView.
        """
        client.Script(f"window.__obs?.hookVtkjs('{ref}')")

    def _on_render_start(self, *_):
        self._render_start = time.perf_counter()

    def _on_render_end(self, *_):
        if self._render_start is not None:
            self._renders.append((time.perf_counter() - self._render_start) * 1000)
            del self._renders[:-1000]
            self._render_start = None

    def _on_report(self, event):
        event = {"time": time.time(), **self.base, **event}
        renders, self._renders = self._renders, []
        if event.get("type") == "interaction" and event.get("mode") == "remote":
            renders.sort()
            event["server_render_call"] = {
                "count": len(renders),
                "ms_mean": round(sum(renders) / len(renders), 1) if renders else None,
                "ms_p95": round(renders[int(0.95 * (len(renders) - 1))], 1)
                if renders
                else None,
            }

        line = json.dumps(event)
        print(f"OBS {line}" if self.verbose else summarize(event), flush=True)
        if self.log:
            self.log.parent.mkdir(parents=True, exist_ok=True)
            with self.log.open("a") as f:
                f.write(line + "\n")


def summarize(event):
    """One short line describing a measurement."""

    def ms(value):
        return "–" if value is None else f"{value:.0f} ms"

    head = f"[obs] {event.get('mode')} · {event.get('api') or '?'}"
    kind = event.get("type")
    if kind == "first_frame":
        since = " (after switch)" if event.get("since") == "switch" else ""
        return f"{head} · first frame {ms(event.get('ms'))}{since}"
    if kind == "interaction":
        fps = event.get("fps")
        fps = "–" if fps is None else f"{fps:.0f}"
        line = (
            f"{head} · {event.get('input')} {fps} fps"
            f" (p95 {ms(event.get('frame_ms_p95'))})"
        )
        render = event.get("server_render_call")
        if render and render.get("ms_mean") is not None:
            line += f" · server render {render['ms_mean']:.1f} ms"
        return line
    return f"{head} · {kind}"


def observe_simple_viewer(viewer, demo, rendering, server_backend):
    """Set up the observability of a trame-pyvista SimpleViewer."""
    obs = Observability(
        viewer.server, demo, rendering, server_backend, viewer.plotter.render_window
    )
    viewer.view_wasm.updated = SCENE_READY
    with viewer.ui:
        obs.watch_mode(f"{viewer.RENDERING_MODE} === 'remote'")
    return obs
