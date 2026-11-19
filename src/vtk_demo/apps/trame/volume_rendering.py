"""Volume rendering of a CT or MRI with 3D Slicer's presets, rendered by VTK.wasm.

The dataset and the CT-Chest-Contrast-Enhanced preset are the ones of
https://discourse.vtk.org/t/how-show-the-bone-of-a-serial-dicom-files/4802:
3D Slicer's CTChest sample, read straight from its scene bundle (``.mrb``).
The volume is sent once; changing the preset, its shift or the shading only
sends the new volume property to the browser, where VTK.wasm ray casts the
volume.

Any other 3D Slicer sample holding a 3D scalar volume (NRRD file or scene
bundle) can be rendered instead, by its dataset name;
``--dataset list`` lists them. MRI scans start with the MR-Default preset.

    vtk-demo run trame.volume-rendering             # VTK.wasm on WebGL 2
    vtk-demo run trame.volume-rendering --webgpu    # same thing on WebGPU
    vtk-demo run trame.volume-rendering --dataset list
    vtk-demo run trame.volume-rendering --dataset mr-head-scene
"""

import sys

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify4 import VAppLayout
from trame.widgets import vtklocal
from trame.widgets import vuetify4 as v4
from vtkmodules.vtkRenderingCore import (
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

import vtkmodules.vtkInteractionStyle  # noqa: F401 isort:skip
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401 isort:skip

from vtk_demo import data
from vtk_demo.io.nrrd import read_volume
from vtk_demo.scenes.volume_rendering import (
    DEFAULT_MR_PRESET,
    DEFAULT_PRESET,
    PRESETS,
    build_volume_rendering_scene,
)

DATASET = "ct-chest-scene"


def dataset_listing(names):
    """One line per dataset: name, download size, modality and description.

    A ``*`` marks the datasets already downloaded.
    """
    datasets = sorted((data.get(name) for name in names), key=lambda ds: ds.name)
    width = max(len(ds.name) for ds in datasets)
    lines = []
    for ds in datasets:
        local = "*" if ds.is_local else " "
        size = f"{ds.size / 1e6:4.0f} MB" if ds.size else "     ?"
        modality = "MRI" if "mri" in ds.tags else "CT" if "ct" in ds.tags else ""
        lines.append(
            f"{local} {ds.name:<{width}}  {size}  {modality:<3}  {ds.meta.description}"
        )
    lines.append("\n(* already downloaded)")
    return "\n".join(lines)


class VolumeRenderingDemo(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")
        self.server.cli.add_argument(
            "--webgpu", action="store_true", help="Render with WebGPU in the browser"
        )
        self.server.cli.add_argument(
            "--dataset",
            default=DATASET,
            metavar="NAME",
            help=f"3D Slicer sample to render (default: {DATASET}); "
            "'--dataset list' lists the available ones",
        )
        args, _ = self.server.cli.parse_known_args()
        self.rendering = "webgpu" if args.webgpu else "webgl"

        names = data.medical.scalar_volumes()
        if args.dataset == "list":
            print(dataset_listing(names))
            raise SystemExit(0)
        if args.dataset not in names:
            print(
                f"Unknown dataset {args.dataset!r}, choose one of:\n\n"
                + dataset_listing(names),
                file=sys.stderr,
            )
            raise SystemExit(2)

        dataset = data.get(args.dataset)
        data.print_usage(dataset)
        image = read_volume(dataset.path)
        self.dataset = dataset.name
        self.unit = "" if "mri" in dataset.tags else " HU"
        preset = DEFAULT_MR_PRESET if "mri" in dataset.tags else DEFAULT_PRESET

        self.renderer = vtkRenderer()
        self.vr = build_volume_rendering_scene(self.renderer, image, preset)
        self.render_window = vtkRenderWindow(off_screen_rendering=True)
        self.render_window.AddRenderer(self.renderer)
        interactor = vtkRenderWindowInteractor(render_window=self.render_window)
        interactor.interactor_style.SetCurrentStyleToTrackballCamera()

        camera = self.renderer.active_camera
        self.initial_camera = (
            camera.position,
            camera.focal_point,
            camera.view_up,
            camera.view_angle,
        )

        self.state.update(
            dict(
                presets=list(PRESETS),
                preset=preset,
                shift=0,
                shade=self.vr.shade,
                dims=" × ".join(str(d) for d in image.GetDimensions()),
            )
        )
        self._build_ui()

    @change("preset", "shift")
    def _on_transfer_function(self, preset, shift, **_):
        self.vr.preset = preset
        self.vr.shift = float(shift)
        self.ctx.view.update_throttle()

    @change("shade")
    def _on_shade(self, shade, **_):
        self.vr.shade = shade
        self.ctx.view.update()

    def reset_camera(self):
        """Back to the initial front view.

        The camera only moves in the browser, so the server one still holds
        the initial view: mark it modified so that it is sent again.
        """
        camera = self.renderer.active_camera
        (
            camera.position,
            camera.focal_point,
            camera.view_up,
            camera.view_angle,
        ) = self.initial_camera
        camera.Modified()
        self.ctx.view.update(push_camera=True)

    def _build_ui(self):
        self.state.trame__title = "VTK.wasm volume rendering"
        with VAppLayout(self.server, full_height=True) as self.ui:
            with v4.VMain(classes="position-relative"):
                vtklocal.LocalView(
                    self.render_window,
                    ctx_name="view",
                    config=(f"{{ rendering: '{self.rendering}', exec: 'async' }}",),
                )
                v4.VBtn(
                    icon="mdi-crop-free",
                    variant="elevated",
                    density="comfortable",
                    title="Reset camera",
                    click=self.reset_camera,
                    style="position: absolute; top: 1rem; left: 1rem; z-index: 1;",
                    classes="rounded",
                )
                v4.VChip(
                    f"{self.dataset} · VTK.wasm · {self.rendering} · {{{{ dims }}}} voxels",
                    style="position: absolute; top: 1rem; right: 1rem;",
                    variant="outlined",
                )

            with v4.VFooter(app=True, classes="d-flex align-center ga-4"):
                v4.VProgressLinear(
                    indeterminate=True,
                    absolute=True,
                    location="top",
                    active=("trame__busy",),
                )
                v4.VSelect(
                    v_model="preset",
                    items=("presets",),
                    label="Preset",
                    hide_details=True,
                    density="compact",
                    style="max-width: 18rem;",
                    variant="outlined",
                )
                v4.VSwitch(
                    v_model="shade",
                    label="Shade",
                    color="primary",
                    hide_details=True,
                    density="compact",
                    classes="flex-grow-0",
                )
                v4.VLabel(f"Shift: {{{{ shift }}}}{self.unit}", style="width: 8rem;")
                v4.VSlider(
                    v_model="shift",
                    min=-1000,
                    max=1000,
                    step=1,
                    hide_details=True,
                    density="compact",
                )
                v4.VBtn(
                    icon="mdi-restore",
                    variant="text",
                    density="compact",
                    click="shift = 0",
                )


def main():
    VolumeRenderingDemo().server.start()


if __name__ == "__main__":
    main()
