"""Bearing assembly: VTK.wasm transparency, toggling between WebGL and WebGPU.

Port of the "Bearing assembly" example of the vtk.js deep transparency gallery
(https://github.com/PaulHax/vtk-js-deep-transparency). The races, balls and
retainer cage of a parametric ball bearing are drawn by two VTK.wasm views
stacked on top of each other, and a toggle picks the one on display:

- WebGL 2: weighted blended order-independent transparency, VTK's default,
  which averages the translucent layers of a pixel without sorting them;
- WebGPU: the deep framebuffer of ``vtkWebGPURenderer``, an A-buffer that
  sorts the 16 nearest fragments of each pixel and composites them front to
  back, in a single geometry pass. See
  https://www.kitware.com/better-transparency-with-vtk-and-webgpu/

Colors, opacities and view direction come from the ``manifest.json`` of the
``bearing-assembly`` dataset. Both views share the actors and the camera of
the server scene, and stay loaded: the camera moved in the view on display is
pushed to the hidden one, so flipping the toggle shows the same viewpoint
right away.

    vtk-demo run trame.bearing-assembly
"""

import json
import math

from trame.app import TrameApp
from trame.ui.vuetify4 import VAppLayout
from trame.widgets import html, vtklocal
from trame.widgets import vuetify4 as v4
from vtkmodules.vtkIOXML import vtkXMLPolyDataReader
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkCamera,
    vtkLight,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

import vtkmodules.vtkInteractionStyle  # noqa: F401 isort:skip
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401 isort:skip

from vtk_demo import data, vtk_version

DATASET = data.get("bearing-assembly")
SCENE = "cad"  # key of the scene in manifest.json

# Three colored lights, positioned around the scene center in units of its radius
LIGHTS = [
    ((4, 5, 7), 0.7, (1, 0.94, 0.86)),
    ((-5, 1, 3), 0.3, (0.67, 0.82, 1)),
    ((0, -4, -4), 0.5, (0.69, 1, 0.93)),
]

# (rendering backend of the view, toggle label, title, detail)
VIEWS = [
    ("webgl", "WebGL", "Weighted blend", "Depth-weighted average, unsorted"),
    ("webgpu", "WebGPU", "Deep framebuffer", "Depth-sorted, nearest 16 fragments"),
]

# Camera properties restored by the reset button
CAMERA_PROPERTIES = ("position", "focal_point", "view_up", "view_angle")

data.print_usage(DATASET)


class BearingAssembly(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")
        manifest = json.loads((DATASET.path / "manifest.json").read_text())
        self.scene = manifest["scenes"][SCENE]
        self.views = []  # one LocalView per entry of VIEWS
        self.state.backend = len(VIEWS) - 1  # index in VIEWS of the view on display
        self._build_scene()
        self._build_ui()

    # -------------------------------------------------------------------------
    # VTK pipeline
    # -------------------------------------------------------------------------

    def _build_scene(self):
        self.actors = [self._layer_actor(layer) for layer in self.scene["actors"]]
        self.state.layers = [
            {
                "label": layer["label"],
                "color": _hex(layer["color"]),
                "triangles": layer["triangleCount"],
            }
            for layer in self.scene["actors"]
        ]
        self.state.opacities = [layer["opacity"] for layer in self.scene["actors"]]
        self.state.visibilities = [True] * len(self.actors)
        # GetBounds() runs the readers: count triangles after it
        bounds = _union_bounds([actor.GetBounds() for actor in self.actors])
        self.state.n_triangles = sum(
            actor.mapper.input.GetNumberOfPolys() for actor in self.actors
        )
        center = [(bounds[2 * i] + bounds[2 * i + 1]) / 2 for i in range(3)]
        radius = math.dist(center, bounds[1::2])

        # One render window per view, sharing actors and camera
        self.camera = vtkCamera()
        self.render_windows = []
        for _ in VIEWS:
            renderer = vtkRenderer(
                background=self.scene["background"],
                automatic_light_creation=False,
            )
            renderer.SetActiveCamera(self.camera)
            for position, intensity, color in LIGHTS:
                light = vtkLight(
                    position=[
                        c + p * radius for c, p in zip(center, position, strict=True)
                    ],
                    focal_point=center,
                    intensity=intensity,
                    color=color,
                )
                light.SetLightTypeToSceneLight()
                renderer.AddLight(light)
            for actor in self.actors:
                renderer.AddActor(actor)

            render_window = vtkRenderWindow(off_screen_rendering=True)
            render_window.AddRenderer(renderer)
            interactor = vtkRenderWindowInteractor(render_window=render_window)
            interactor.interactor_style.SetCurrentStyleToTrackballCamera()
            self.render_windows.append(render_window)

        # Look along the manifest view direction, then fit the bearing in view
        direction = self.scene["viewDirection"]
        self.camera.focal_point = center
        self.camera.position = [c + d for c, d in zip(center, direction, strict=True)]
        self.camera.view_up = self.scene["viewUp"]
        self.render_windows[0].renderers.GetFirstRenderer().ResetCamera()
        self.initial_camera = tuple(
            getattr(self.camera, name) for name in CAMERA_PROPERTIES
        )
        self._apply_camera(self.initial_camera)

    @staticmethod
    def _layer_actor(layer):
        file_name = layer["url"].split("/")[-1]
        reader = vtkXMLPolyDataReader(file_name=DATASET.path / file_name)
        mapper = vtkPolyDataMapper(scalar_visibility=False)
        reader >> mapper
        actor = vtkActor(mapper=mapper)
        actor.property.color = layer["color"]
        actor.property.opacity = layer["opacity"]
        actor.property.ambient = 0.2
        actor.property.diffuse = 0.8
        actor.property.specular = 0.3
        actor.property.specular_power = 35
        actor.property.metallic = 0.08
        actor.property.roughness = 0.38
        actor.property.SetInterpolationToPBR()
        return actor

    def _apply_camera(self, values):
        for name, value in zip(CAMERA_PROPERTIES, values, strict=True):
            setattr(self.camera, name, value)
        for render_window in self.render_windows:
            render_window.renderers.GetFirstRenderer().ResetCameraClippingRange()

    # -------------------------------------------------------------------------
    # Controller
    # -------------------------------------------------------------------------

    def _on_camera(self, index, camera_state):
        """Camera moved in view ``index``: move the camera of the hidden views.

        Only the view on display drives the camera. The hidden views report
        the camera pushed to them, which is ignored to avoid a ping-pong.
        """
        if index != self.state.backend:
            return
        self.views[index].vtk_update_from_state(camera_state)
        for i, view in enumerate(self.views):
            if i != index:
                view.update(push_camera=True)

    def reset_camera(self):
        """Back to the initial view, in all views."""
        self._apply_camera(self.initial_camera)
        self._update_views(push_camera=True)

    def set_opacity(self, index, opacity):
        opacities = list(self.state.opacities)
        opacities[index] = float(opacity)
        self.state.opacities = opacities
        self.actors[index].property.opacity = opacities[index]
        self._update_views()

    def toggle_visibility(self, index):
        visibilities = list(self.state.visibilities)
        visibilities[index] = not visibilities[index]
        self.state.visibilities = visibilities
        self.actors[index].visibility = visibilities[index]
        self._update_views()

    def _update_views(self, **kwargs):
        for view in self.views:
            view.update(**kwargs)

    # -------------------------------------------------------------------------
    # UI
    # -------------------------------------------------------------------------

    def _build_ui(self):
        scene = self.scene
        self.state.trame__title = scene["name"]
        with VAppLayout(self.server, full_height=True, theme="dark") as self.ui:
            with v4.VAppBar(density="compact", flat=True, color="#0e131b"):
                v4.VAppBarTitle(scene["name"])
                with v4.VBtnToggle(
                    v_model=("backend",),
                    mandatory=True,
                    density="compact",
                    variant="outlined",
                    divided=True,
                    classes="mr-4",
                ):
                    for i, (_, label, _, _) in enumerate(VIEWS):
                        v4.VBtn(label, value=(i,), size="small")
                v4.VChip(
                    "VTK.wasm · {{ n_triangles.toLocaleString() }} triangles",
                    variant="outlined",
                    size="small",
                    classes="mr-4",
                )

            with v4.VMain():
                with html.Div(classes="fill-height position-relative"):
                    for i, (rendering, _, title, detail) in enumerate(VIEWS):
                        self._view_panel(i, rendering, title, detail)
                    v4.VBtn(
                        icon="mdi-crop-free",
                        variant="elevated",
                        density="comfortable",
                        title="Reset camera",
                        click=self.reset_camera,
                        style="position: absolute; bottom: 1rem; left: 1rem; z-index: 1;",
                        classes="rounded",
                    )

            with v4.VFooter(app=True, classes="d-flex flex-column align-stretch pa-3"):
                v4.VProgressLinear(
                    indeterminate=True,
                    absolute=True,
                    location="top",
                    active=("trame__busy",),
                )
                html.Div(
                    f"{scene['description']} {scene['note']}",
                    classes="text-body-2 mb-2",
                )
                self._layer_controls()
                html.Div(
                    f"{scene['credit']} {scene['attributionNote']}",
                    classes="text-caption text-medium-emphasis mt-2",
                )

    def _view_panel(self, index, rendering, title, detail):
        # Hidden views keep their size (visibility, not display: none), so they
        # are ready to be shown without a resize
        with html.Div(
            style=(
                f"{{ position: 'absolute', inset: 0, "
                f"visibility: backend === {index} ? 'visible' : 'hidden' }}",
            ),
        ):
            view = vtklocal.LocalView(
                self.render_windows[index],
                config=(f"{{ rendering: '{rendering}', exec: 'async' }}",),
                camera=(self._on_camera, f"[{index}, $event]"),
            )
            self.views.append(view)
            with html.Div(
                style="position: absolute; top: 1rem; left: 1rem; "
                "pointer-events: none;",
                classes="text-body-2",
            ):
                html.Div(title, classes="font-weight-bold")
                html.Div(detail, classes="text-medium-emphasis")

    def _layer_controls(self):
        with html.Div(
            v_for="(layer, i) in layers",
            key="i",
            classes="d-flex align-center ga-3",
        ):
            v4.VBtn(
                icon=("visibilities[i] ? 'mdi-eye' : 'mdi-eye-off'",),
                variant="text",
                density="compact",
                title=("`${visibilities[i] ? 'Hide' : 'Show'} ${layer.label}`",),
                click=(self.toggle_visibility, "[i]"),
            )
            html.Span(
                style=(
                    "{ background: layer.color, width: '0.8rem', "
                    "height: '0.8rem', borderRadius: '2px', flex: 'none' }",
                ),
            )
            html.Span(
                "{{ layer.label }}",
                classes="text-body-2",
                style="width: 9rem; flex: none;",
            )
            html.Span(
                "{{ layer.triangles.toLocaleString() }} triangles",
                classes="text-caption text-medium-emphasis",
                style="width: 8rem; flex: none; white-space: nowrap;",
            )
            v4.VSlider(
                model_value=("opacities[i]",),
                update_modelValue=(self.set_opacity, "[i, $event]"),
                min=0,
                max=1,
                step=0.01,
                hide_details=True,
                density="compact",
                disabled=("!visibilities[i]",),
            )
            html.Span(
                "{{ Math.round(opacities[i] * 100) }}%",
                classes="text-body-2 text-right",
                style="width: 3rem; flex: none;",
            )


def _hex(color):
    return "#" + "".join(f"{round(c * 255):02x}" for c in color)


def _union_bounds(all_bounds):
    return [(min if i % 2 == 0 else max)(b[i] for b in all_bounds) for i in range(6)]


def main():
    vtk_version.check(
        "trame.bearing-assembly",
        vtk_version.WEBGPU_DEEP_FRAMEBUFFER,
        "older VTK has no WebGPU deep framebuffer, the WebGPU view is unsorted",
    )
    BearingAssembly().server.start()


if __name__ == "__main__":
    main()
