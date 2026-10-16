"""Interactive isosurface in a native desktop window, with a Dear ImGui UI.

The same scene as ``trame.contour``, without a browser: VTK renders into the
OpenGL context of the ImGui window, and the contour is recomputed when the
slider moves.

    vtk-demo run imgui.contour
"""

import argparse

from imgui_bundle import hello_imgui, imgui, immapp
from vtkmodules.vtkRenderingCore import vtkRenderer

from vtk_demo.scenes import build_isosurface_scene

from .viewport import Viewport

TITLE = "VTK contour"


class ContourDemo:
    def __init__(self):
        renderer = vtkRenderer(background=(1, 1, 1))
        self.iso = build_isosurface_scene(renderer)
        self.viewport = Viewport(renderer)

    def gui(self):
        footer = (
            imgui.get_frame_height_with_spacing() + imgui.get_style().window_padding.y
        )
        avail = imgui.get_content_region_avail()
        self.viewport.draw(imgui.ImVec2(avail.x, avail.y - footer))
        self._chip()
        self._footer()

    def _chip(self):
        """Statistics in the top right corner of the view."""
        text = f"VTK · OpenGL · {self.iso.n_triangles:,} triangles"
        padding = imgui.get_style().frame_padding
        size = imgui.calc_text_size(text)
        corner = imgui.get_window_pos()
        width = imgui.get_window_width()
        margin = imgui.get_font_size()
        p_max = imgui.ImVec2(
            corner.x + width - margin, corner.y + margin + size.y + 2 * padding.y
        )
        p_min = imgui.ImVec2(p_max.x - size.x - 4 * padding.x, corner.y + margin)
        draw = imgui.get_window_draw_list()
        rounding = p_max.y - p_min.y
        draw.add_rect_filled(
            p_min, p_max, imgui.get_color_u32(imgui.Col_.window_bg), rounding
        )
        draw.add_rect(p_min, p_max, imgui.get_color_u32(imgui.Col_.text), rounding)
        draw.add_text(
            imgui.ImVec2(p_min.x + 2 * padding.x, p_min.y + padding.y),
            imgui.get_color_u32(imgui.Col_.text),
            text,
        )

    def _footer(self):
        imgui.align_text_to_frame_padding()
        imgui.text(f"Iso value: {self.iso.value:,.1f}")
        imgui.same_line(10 * imgui.get_font_size())
        imgui.set_next_item_width(-1)
        low, high = self.iso.data_range
        changed, value = imgui.slider_float("##iso", self.iso.value, low, high, "")
        if changed:
            self.iso.value = value


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args()

    demo = ContourDemo()
    params = hello_imgui.RunnerParams()
    params.app_window_params.window_title = TITLE
    params.app_window_params.window_geometry.size = (1280, 800)
    params.imgui_window_params.default_imgui_window_type = (
        hello_imgui.DefaultImGuiWindowType.provide_full_screen_window
    )
    params.imgui_window_params.tweaked_theme.theme = (
        hello_imgui.ImGuiTheme_.white_is_white
    )
    params.ini_disable = True  # no window layout to save
    params.callbacks.show_gui = demo.gui
    immapp.run(params)


if __name__ == "__main__":
    main()
