"""Live threshold of an FEA result: VTK filter on the server, VTK.wasm rendering in the browser.

The bracket of the ``fea-bracket`` dataset is clipped to the cells whose
von Mises stress lies within the range slider. ``vtkThreshold`` runs in Python
when the slider moves; only the new geometry travels to the browser, where
VTK.wasm renders it along with the scalar bar of the stress.
Camera interaction never touches the server.

    vtk-demo run trame.live-processing             # VTK.wasm on WebGL 2
    vtk-demo run trame.live-processing --webgpu    # same thing on WebGPU
"""

from trame.app import TrameApp
from trame.decorators import change
from trame.ui.vuetify4 import VAppLayout
from trame.widgets import vtklocal
from trame.widgets import vuetify4 as v4
from vtkmodules.vtkCommonDataModel import vtkDataObject
from vtkmodules.vtkFiltersCore import vtkFeatureEdges, vtkThreshold
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader
from vtkmodules.vtkRenderingAnnotation import vtkScalarBarActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkCoordinate,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkTextActor,
)

import vtkmodules.vtkInteractionStyle  # noqa: F401 isort:skip
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401 isort:skip

from vtk_demo import data
from vtk_demo.lut import lookup_table

# Dataset
DATASET = data.get("fea-bracket")
FIELD = "Equivalent (von-Mises) Stress (psi)"  # the only cell array of fea-bracket

# Scalar bar layout, in pixels from the bottom of the view
BAR_MARGIN = 8
BAR_HEIGHT = 56  # colors and labels below them
TITLE_GAP = 4

# Provide information about data
data.print_usage(DATASET)


class LiveProcessing(TrameApp):
    def __init__(self, server=None):
        super().__init__(server, client_type="vue3")
        self.server.cli.add_argument(
            "--webgpu", action="store_true", help="Render with WebGPU in the browser"
        )
        args, _ = self.server.cli.parse_known_args()
        self.rendering = "webgpu" if args.webgpu else "webgl"

        self._build_scene()
        self.state.data_range = list(self.data_range)
        self.state.threshold_range = list(self.data_range)
        self._apply_threshold(self.data_range)
        self._build_ui()

    # -------------------------------------------------------------------------
    # VTK pipeline
    # -------------------------------------------------------------------------

    def _build_scene(self):
        reader = vtkXMLUnstructuredGridReader(file_name=DATASET.path)
        reader.Update()
        mesh = reader.GetOutput()
        self.data_range = mesh.GetCellData().GetArray(FIELD).GetRange()

        self.threshold = vtkThreshold()
        self.threshold.SetInputArrayToProcess(
            0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_CELLS, FIELD
        )
        self.threshold.SetThresholdFunction(vtkThreshold.THRESHOLD_BETWEEN)
        self.lut = lookup_table("Fast")
        self.mapper = vtkPolyDataMapper(
            lookup_table=self.lut,
            scalar_visibility=True,
            interpolate_scalars_before_mapping=True,
            use_lookup_table_scalar_range=True,  # colors follow self.lut range
        )
        mesh >> self.threshold >> vtkDataSetSurfaceFilter() >> self.mapper
        self.mapper.SetScalarModeToUseCellFieldData()
        self.mapper.SelectColorArray(FIELD)
        actor = vtkActor(mapper=self.mapper)

        # Silhouette of the whole part, for context once cells are removed
        edges = vtkFeatureEdges(
            boundary_edges=True,
            feature_edges=True,
            feature_angle=30,
            manifold_edges=False,
            non_manifold_edges=False,
            coloring=False,
        )
        edges_mapper = vtkPolyDataMapper(scalar_visibility=False)
        mesh >> vtkDataSetSurfaceFilter() >> edges >> edges_mapper
        edges_actor = vtkActor(mapper=edges_mapper)
        edges_actor.property.color = (0.35, 0.35, 0.4)
        edges_actor.property.opacity = 0.6

        self.scalar_bar = vtkScalarBarActor(
            lookup_table=self.lut,
            title=" ",  # an empty title makes vtkScalarBarActor skip the labels
            number_of_labels=7,
            label_format="%-#6.3g",
            unconstrained_font_size=True,
            maximum_height_in_pixels=BAR_HEIGHT,
        )
        self.scalar_bar.SetOrientationToHorizontal()
        self.scalar_bar.SetTextPositionToPrecedeScalarBar()  # labels below the colors
        _place(self.scalar_bar.position_coordinate, (0.05, 0), (0, BAR_MARGIN))
        self.scalar_bar.SetWidth(0.9)
        self.scalar_bar.SetHeight(1)  # capped by maximum_height_in_pixels
        labels = self.scalar_bar.label_text_property
        labels.color = (0.15, 0.15, 0.18)
        labels.shadow = False
        labels.italic = False
        labels.font_size = 14

        title = vtkTextActor(input=FIELD)
        _place(
            title.position_coordinate,
            (0.5, 0),
            (0, BAR_MARGIN + BAR_HEIGHT + TITLE_GAP),
        )
        title.text_property.color = (0.15, 0.15, 0.18)
        title.text_property.font_size = 22
        title.text_property.bold = True
        title.text_property.justification = 1  # centered
        title.text_property.vertical_justification = 0  # bottom

        self.renderer = vtkRenderer(background=(0.78, 0.79, 0.82))
        self.renderer.SetBackground2(0.97, 0.97, 0.98)
        self.renderer.SetGradientBackground(True)
        self.renderer.AddActor(actor)
        self.renderer.AddActor(edges_actor)
        self.renderer.AddViewProp(self.scalar_bar)
        self.renderer.AddViewProp(title)

        self.render_window = vtkRenderWindow(off_screen_rendering=True)
        self.render_window.AddRenderer(self.renderer)
        interactor = vtkRenderWindowInteractor(render_window=self.render_window)
        interactor.interactor_style.SetCurrentStyleToTrackballCamera()

        self.renderer.ResetCamera()
        camera = self.renderer.active_camera
        camera.Elevation(-90)
        self.renderer.ResetCamera()
        camera.Azimuth(30)
        camera.Elevation(15)
        self.renderer.ResetCamera()
        self.initial_camera = (
            camera.position,
            camera.focal_point,
            camera.view_up,
            camera.parallel_scale,
        )

    # -------------------------------------------------------------------------
    # State handlers
    # -------------------------------------------------------------------------

    @change("threshold_range")
    def _on_threshold(self, threshold_range, **_):
        self._apply_threshold(threshold_range)
        self.ctx.view.update()

    def reset_camera(self):
        """Back to the initial view of the whole bracket.

        The camera only moves in the browser, so the server one still holds
        the initial view: mark it modified so that it is sent again.
        """
        camera = self.renderer.active_camera
        (
            camera.position,
            camera.focal_point,
            camera.view_up,
            camera.parallel_scale,
        ) = self.initial_camera
        camera.Modified()
        self.ctx.view.update(push_camera=True)

    def _apply_threshold(self, threshold_range):
        self.threshold.SetLowerThreshold(threshold_range[0])
        self.threshold.SetUpperThreshold(threshold_range[1])
        self.threshold.Update()
        ds = self.threshold.GetOutput()

        # Colors span the selected range: the mapper uses the lookup table
        # range, which the scalar bar shows as well
        low, high = threshold_range
        if high <= low:  # both thumbs on the same value
            high = low + 1e-6 * max(abs(low), 1)
        self.lut.SetRange(low, high)

        self.state.n_cells = ds.GetNumberOfCells()

    # -------------------------------------------------------------------------
    # UI
    # -------------------------------------------------------------------------

    def _build_ui(self):
        self.state.trame__title = "VTK.wasm live processing"
        fmt = "toLocaleString(undefined, { maximumFractionDigits: 1 })"
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
                    f"VTK.wasm · {self.rendering} · {{{{ n_cells.toLocaleString() }}}} cells",
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
                v4.VLabel(f"{{{{ threshold_range[0].{fmt} }}}}")
                v4.VRangeSlider(
                    v_model="threshold_range",
                    min=("data_range[0]",),
                    max=("data_range[1]",),
                    step=("(data_range[1] - data_range[0]) / 255",),
                    strict=True,
                    hide_details=True,
                    density="compact",
                )
                v4.VLabel(f"{{{{ threshold_range[1].{fmt} }}}}")


def _place(coordinate, anchor, offset):
    """Set ``coordinate`` at ``offset`` pixels from ``anchor``, in normalized viewport."""
    reference = vtkCoordinate(value=(*anchor, 0))
    reference.SetCoordinateSystemToNormalizedViewport()
    coordinate.SetCoordinateSystemToDisplay()
    coordinate.SetReferenceCoordinate(reference)
    coordinate.SetValue(*offset, 0)


def main():
    LiveProcessing().server.start()


if __name__ == "__main__":
    main()
