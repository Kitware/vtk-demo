"""Standalone export: one HTML file, VTK.wasm + WebGPU, no server.

The VTK scene is serialized, then bundled together with the VTK.wasm runtime
into a single HTML file you can e-mail, attach to a report or drop on any
static host. Rendering happens 100% in the browser.

    vtk-demo run export.bunny-html                     # writes exports/bunny-*.html
    vtk-demo run export.bunny-html --output /tmp/out
    open exports/bunny-webgpu.html
"""

import argparse
from pathlib import Path

import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingCore import vtkRenderer, vtkRenderWindow
from vtkmodules.vtkRenderingUI import vtkGenericRenderWindowInteractor

from vtk_demo.scenes import build_bunny_scene


def scene_window(build, size=(1280, 800)):
    """An off screen ``vtkRenderWindow`` with the scene ``build(renderer)`` in it.

    It gets an interactor with the trackball camera style, which the exported
    page uses to orbit the camera.
    """
    renderer = vtkRenderer()
    build(renderer)
    window = vtkRenderWindow(size=size, off_screen_rendering=True)
    window.AddRenderer(renderer)
    vtkGenericRenderWindowInteractor(
        render_window=window, interactor_style=vtkInteractorStyleTrackballCamera()
    )
    window.Render()
    return window


def export_html(window, output, rendering="webgpu", mode="wasm32"):
    """Write ``window`` as a self-contained VTK.wasm HTML page. Returns the path."""
    from trame_vtklocal.utils import exporter

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    exporter.to_html(
        [window],
        output=output,
        config={"mode": mode, "rendering": rendering, "exec": "async"},
    )
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output", type=Path, default=Path("exports"), help="Output directory"
    )
    args = parser.parse_args()

    window = scene_window(build_bunny_scene)
    for rendering in ("webgpu", "webgl"):
        output = export_html(window, args.output / f"bunny-{rendering}.html", rendering)
        print(f"Wrote {output} ({output.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
