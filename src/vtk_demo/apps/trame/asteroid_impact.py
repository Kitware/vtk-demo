"""Asteroid ocean impact: VTK.wasm transparency on WebGL vs. WebGPU, side by side.

Port of the "Asteroid ocean impact" example of the vtk.js deep transparency
gallery (https://github.com/PaulHax/vtk-js-deep-transparency). Water,
temperature and asteroid isosurfaces of the LANL deep water impact
simulation are drawn by two VTK.wasm views with a linked camera:

- left, WebGL 2: weighted blended order-independent transparency, VTK's
  default, which averages the translucent layers of a pixel without sorting
  them;
- right, WebGPU: the deep framebuffer of ``vtkWebGPURenderer``, an A-buffer
  that sorts the 16 nearest fragments of each pixel and composites them front
  to back, in a single geometry pass. See
  https://www.kitware.com/better-transparency-with-vtk-and-webgpu/

Colors, opacities, lights and camera come from the ``manifest.json`` of the
``asteroid-impact-surfaces`` dataset. Both views share the actors and the
camera of the server scene: visibility and opacity changes only send the
modified properties, and a camera moved in one view is pushed to the other.

    vtk-demo run trame.asteroid-impact
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

from vtk_demo import data

DATASET = data.get("asteroid-impact-surfaces")
SCENE = "impact"  # key of the scene in manifest.json

# Three colored lights, positioned around the scene center in units of its radius
LIGHTS = [
    ((4, 5, 7), 0.7, (1, 0.94, 0.86)),
    ((-5, 1, 3), 0.3, (0.67, 0.82, 1)),
    ((0, -4, -4), 0.5, (0.69, 1, 0.93)),
]

# (rendering backend of the view, title, detail)
VIEWS = [
    ("webgl", "WebGL · Weighted blend", "Depth-weighted average, unsorted"),
    ("webgpu", "WebGPU · Deep framebuffer", "Depth-sorted, nearest 16 fragments"),
]

# Camera properties kept in sync between the views
CAMERA_PROPERTIES = ("position", "focal_point", "view_up", "parallel_scale")

data.print_usage(DATASET)


class AsteroidImpact(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")
        manifest = json.loads((DATASET.path / "manifest.json").read_text())
        self.scene = manifest["scenes"][SCENE]
        self.views = []  # one LocalView per entry of VIEWS
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
                "field": layer["field"],
                "isovalue": layer["isovalue"],
            }
            for layer in self.scene["actors"]
        ]
        self.state.opacities = [layer["opacity"] for layer in self.scene["actors"]]
        self.state.visibilities = [True] * len(self.actors)
        self.state.n_triangles = sum(
            actor.mapper.input.GetNumberOfPolys() for actor in self.actors
        )

        bounds = _union_bounds([actor.GetBounds() for actor in self.actors])
        mid = [(bounds[2 * i] + bounds[2 * i + 1]) / 2 for i in range(3)]
        radius = math.dist(mid, bounds[1::2])
        center = self.scene.get("cameraFocalPoint", mid)

        # One render window per view, sharing actors and camera
        self.camera = vtkCamera(parallel_projection=True)
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

        direction = self.scene["viewDirection"]
        self.initial_camera = (
            [c + d * radius * 3 for c, d in zip(center, direction, strict=True)],
            center,
            self.scene["viewUp"],
            self.scene["parallelScale"],
        )
        self._apply_camera(self.initial_camera)

    @staticmethod
    def _layer_actor(layer):
        file_name = layer["url"].split("/")[-1]
        reader = vtkXMLPolyDataReader(
            file_name=DATASET.path / file_name
        )
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

    def _camera_values(self):
        return tuple(_round(getattr(self.camera, name)) for name in CAMERA_PROPERTIES)

    def _apply_camera(self, values):
        for name, value in zip(CAMERA_PROPERTIES, values, strict=True):
            setattr(self.camera, name, value)
        for render_window in self.render_windows:
            render_window.renderers.GetFirstRenderer().ResetCameraClippingRange()

    # -------------------------------------------------------------------------
    # Controller
    # -------------------------------------------------------------------------

    def _on_camera(self, index, camera_state):
        """Camera moved in view ``index``: move the camera of the other views.

        Pushing a camera makes the receiving view report it back: values
        already on the server are dropped, which ends the ping-pong.
        """
        before = self._camera_values()
        self.views[index].vtk_update_from_state(camera_state)
        if self._camera_values() == before:
            return
        for i, view in enumerate(self.views):
            if i != index:
                view.update(push_camera=True)

    def reset_camera(self):
        """Back to the initial view, in both views."""
        self._apply_camera(self.initial_camera)
        self.camera.Modified()
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
        self.state.trame__title = "Asteroid ocean impact"
        with VAppLayout(self.server, full_height=True, theme="dark") as self.ui:
            with v4.VAppBar(density="compact", flat=True, color="#0e131b"):
                v4.VAppBarTitle(scene["name"])
                v4.VChip(
                    "VTK.wasm · {{ n_triangles.toLocaleString() }} triangles",
                    variant="outlined",
                    size="small",
                    classes="mr-4",
                )

            with v4.VMain():
                with html.Div(classes="d-flex fill-height position-relative"):
                    for i, (rendering, title, detail) in enumerate(VIEWS):
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
                html.Div(scene["description"], classes="text-body-2 mb-2")
                self._layer_controls()
                html.Div(
                    f"{scene['credit']} {scene['attributionNote']}",
                    classes="text-caption text-medium-emphasis mt-2",
                )

    def _view_panel(self, index, rendering, title, detail):
        border = "border-left: 1px solid rgba(255, 255, 255, 0.2);" if index else ""
        with html.Div(
            classes="position-relative fill-height flex-grow-1",
            style=f"flex-basis: 0; min-width: 0; {border}",
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
                "{{ layer.field }} = {{ layer.isovalue }}",
                classes="text-caption text-medium-emphasis",
                style="width: 6rem; flex: none;",
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


def _round(value):
    """Camera property to 9 significant digits, to compare it across round trips."""
    if isinstance(value, (tuple, list)):
        return tuple(_round(v) for v in value)
    return float(f"{value:.9g}")


def _hex(color):
    return "#" + "".join(f"{round(c * 255):02x}" for c in color)


def _union_bounds(all_bounds):
    return [(min if i % 2 == 0 else max)(b[i] for b in all_bounds) for i in range(6)]


def main():
    AsteroidImpact().server.start()


if __name__ == "__main__":
    main()
