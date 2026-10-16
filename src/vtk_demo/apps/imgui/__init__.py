"""Native desktop applications with a Dear ImGui UI (imgui-bundle).

VTK renders in the OpenGL context of the ImGui window: see :mod:`.viewport`.
To add an application, create ``vtk_demo/apps/imgui/<name>.py`` with a
``main()`` function that builds its scene with :mod:`vtk_demo.scenes`, and
register it in :data:`vtk_demo.apps.DEMOS` under the "imgui" group.

Requires the ``imgui`` extra (Python 3.11+): ``pip install "vtk-demo[imgui]"``.
"""
