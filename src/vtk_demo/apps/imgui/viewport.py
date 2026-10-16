"""A VTK render window drawn as an image inside a Dear ImGui window.

VTK renders in the OpenGL context of the ImGui window, into its own
framebuffer: the color texture of that framebuffer is then shown with
``imgui.image()``. Nothing is copied back to the CPU. ImGui mouse events over
the image are forwarded to a ``vtkGenericRenderWindowInteractor``.

    from imgui_bundle import immapp

    viewport = Viewport(renderer)
    immapp.run(lambda: viewport.draw(), window_title="VTK")
"""

from imgui_bundle import imgui
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingOpenGL2 import vtkGenericOpenGLRenderWindow
from vtkmodules.vtkRenderingUI import vtkGenericRenderWindowInteractor

BUTTONS = {
    imgui.MouseButton_.left: ("LeftButtonPressEvent", "LeftButtonReleaseEvent"),
    imgui.MouseButton_.middle: ("MiddleButtonPressEvent", "MiddleButtonReleaseEvent"),
    imgui.MouseButton_.right: ("RightButtonPressEvent", "RightButtonReleaseEvent"),
}
BUTTON_FLAGS = (
    imgui.ButtonFlags_.mouse_button_left
    | imgui.ButtonFlags_.mouse_button_middle
    | imgui.ButtonFlags_.mouse_button_right
)


class Viewport:
    """Render ``renderer`` in the ImGui window, with trackball camera interaction."""

    def __init__(self, renderer):
        self.render_window = vtkGenericOpenGLRenderWindow(multi_samples=0)
        self.render_window.SetFrameBlitModeToNoBlit()  # ImGui draws the result
        # The ImGui context is current whenever draw() is called
        self.render_window.SetIsCurrent(True)
        self.render_window.SetReadyForRendering(True)
        self.render_window.AddRenderer(renderer)
        self.interactor = vtkGenericRenderWindowInteractor(
            render_window=self.render_window,
            interactor_style=vtkInteractorStyleTrackballCamera(),
        )
        # draw() renders every frame: no need for the interactor to render too
        self.interactor.EnableRenderOff()
        self.interactor.Initialize()
        self._pressed = set()
        self._initialized = False

    @property
    def renderer(self):
        return self.render_window.GetRenderers().GetFirstRenderer()

    def draw(self, size=None):
        """Render the scene and show it as an image of ``size`` (default: all available space)."""
        if size is None:
            size = imgui.get_content_region_avail()
        width, height = max(int(size.x), 1), max(int(size.y), 1)
        scale = imgui.get_io().display_framebuffer_scale  # retina displays
        pixels = (max(int(width * scale.x), 1), max(int(height * scale.y), 1))
        if tuple(self.render_window.GetSize()) != pixels:
            self.render_window.SetSize(*pixels)
            self.interactor.SetSize(*pixels)

        origin = imgui.get_cursor_screen_pos()
        # Takes the mouse inputs, so that dragging does not move the window
        imgui.invisible_button("##vtk", (width, height), BUTTON_FLAGS)
        self._forward_events(origin, scale, imgui.is_item_hovered())
        self._render()
        # OpenGL textures start at the bottom: flip them vertically
        imgui.get_window_draw_list().add_image(
            imgui.ImTextureRef(self._texture()),
            origin,
            (origin.x + width, origin.y + height),
            (0, 1),
            (1, 0),
        )

    def _render(self):
        if not self._initialized:  # loads the OpenGL functions VTK uses
            self.render_window.OpenGLInit()
            self._initialized = True
        # ImGui changed the OpenGL state behind VTK's back: resync VTK's cache,
        # then restore what ImGui had once VTK is done
        state = self.render_window.GetState()
        state.Reset()
        state.Push()
        self.render_window.Render()
        state.Pop()

    def _texture(self):
        framebuffer = self.render_window.GetDisplayFramebuffer()
        return framebuffer.GetColorAttachmentAsTextureObject(0).GetHandle()

    def _forward_events(self, origin, scale, hovered):
        io = imgui.get_io()
        if not imgui.is_mouse_pos_valid():  # mouse outside of the window
            return
        x = (io.mouse_pos.x - origin.x) * scale.x
        y = (io.mouse_pos.y - origin.y) * scale.y
        iren = self.interactor
        iren.SetEventInformationFlipY(int(x), int(y), io.key_ctrl, io.key_shift)
        iren.SetAltKey(io.key_alt)

        for button, (press, release) in BUTTONS.items():
            if hovered and imgui.is_mouse_clicked(button):
                self._pressed.add(button)
                getattr(iren, press)()
            elif button in self._pressed and imgui.is_mouse_released(button):
                self._pressed.discard(button)
                getattr(iren, release)()

        if (hovered or self._pressed) and (io.mouse_delta.x or io.mouse_delta.y):
            iren.MouseMoveEvent()
        if hovered and io.mouse_wheel > 0:
            iren.MouseWheelForwardEvent()
        elif hovered and io.mouse_wheel < 0:
            iren.MouseWheelBackwardEvent()
