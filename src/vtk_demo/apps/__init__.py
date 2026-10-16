"""Bundled demo applications, grouped by UI toolkit.

Each demo is a module with a ``main()`` function that reads its options from
``sys.argv``. :data:`DEMOS` lists them for the ``vtk-demo`` launcher, without
importing them: each group has its own optional dependencies. Hidden demos
can be run but are left out of ``vtk-demo list``.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Demo:
    group: str
    name: str
    module: str
    summary: str
    hidden: bool = False

    @property
    def id(self):
        return f"{self.group}.{self.name}"


GROUPS = {
    "trame": "Web applications (trame): VTK.wasm, vtk.js and server side rendering",
    "export": "Standalone exports, no server needed",
    "imgui": "Native desktop applications with a Dear ImGui UI",
}

DEMOS = [
    Demo(
        "trame",
        "contour",
        "vtk_demo.apps.trame.contour",
        "Interactive isosurface of a CT scan, filtered on the server, rendered by VTK.wasm",
    ),
    Demo(
        "trame",
        "galaxy",
        "vtk_demo.apps.trame.galaxy",
        "Tens of millions of points with VTK.wasm 64-bit (wasm64) + WebGPU",
    ),
    Demo(
        "trame",
        "animation",
        "vtk_demo.apps.trame.animation",
        "Wave equation stepped in numpy, streamed to VTK.wasm",
    ),
    Demo(
        "trame",
        "pbr",
        "vtk_demo.apps.trame.pbr",
        "PBR materials and image based lighting, VTK.wasm or server rendering",
    ),
    Demo(
        "trame",
        "pbr-legacy",
        "vtk_demo.apps.trame.pbr_legacy",
        "Same PBR scene, vtk.js or server rendering",
    ),
    Demo(
        "trame",
        "transparency",
        "vtk_demo.apps.trame.transparency",
        "Nested translucent shells, glass and bubbles: depth peeling stress test",
    ),
    Demo(
        "trame",
        "glyph",
        "vtk_demo.apps.trame.glyph",
        "Voxel island of 43k objects drawn with GPU instancing (vtkGlyph3DMapper)",
    ),
    Demo(
        "trame",
        "actor-world",
        "vtk_demo.apps.trame.actor_world",
        "The same island with one actor per object",
        hidden=True,
    ),
    Demo(
        "trame",
        "composite-world",
        "vtk_demo.apps.trame.composite_world",
        "An archipelago of islands in a single composite dataset actor",
        hidden=True,
    ),
    Demo(
        "trame",
        "partition-world",
        "vtk_demo.apps.trame.partition_world",
        "The island cut into N composite partitions",
        hidden=True,
    ),
    Demo(
        "export",
        "bunny-html",
        "vtk_demo.apps.export.bunny_html",
        "Write a self-contained VTK.wasm HTML page (WebGPU and WebGL)",
    ),
    Demo(
        "imgui",
        "contour",
        "vtk_demo.apps.imgui.contour",
        "Interactive isosurface of a CT scan in a native window, rendered by VTK OpenGL",
    ),
]


def find(demo_id):
    """Return the demo named ``group.name``, or just ``name`` when unambiguous."""
    matches = [d for d in DEMOS if demo_id in (d.id, d.name)]
    if len(matches) == 1:
        return matches[0]
    if matches:
        names = ", ".join(d.id for d in matches)
        raise KeyError(f"Ambiguous demo {demo_id!r}: {names}")
    raise KeyError(f"Unknown demo {demo_id!r}, see `vtk-demo list`")
