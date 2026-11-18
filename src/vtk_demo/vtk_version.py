"""Warn when a demo needs a newer VTK than the installed one.

Some demos rely on fixes that are only in VTK nightlies from
https://wheels.vtk.org, which ``pip install vtk-demo`` cannot pull by itself.
They still run on older VTK, so :func:`check` prints a warning with the
command to install a suitable nightly instead of failing.

VTK nightlies are numbered ``major.minor.YYYYMMDD``: a version is compared as
``(major, minor, build)``, build being the date of a nightly or the patch
number of a release. Once a release ships these fixes, raise ``vtk>=`` in
``pyproject.toml`` and drop the checks.
"""

import sys

# Nightly tested with the demos, pinned by [tool.uv] in pyproject.toml
NIGHTLY = "9.7.20261101.dev0"
INDEX_URL = "https://wheels.vtk.org"

# Minimum (major, minor, build) for each known issue
VTK_WASM_ARRAY_UPDATES = (9, 7, 2)  # VTK.wasm drew the first frame forever up to 9.7.1
WEBGPU_DEEP_FRAMEBUFFER = (9, 7, 20261011)  # nightly of 2026-10-11


def installed():
    """``(major, minor, build)`` of the VTK in use."""
    from vtkmodules.vtkCommonCore import vtkVersion

    return (
        vtkVersion.GetVTKMajorVersion(),
        vtkVersion.GetVTKMinorVersion(),
        vtkVersion.GetVTKBuildVersion(),
    )


def install_command():
    return f'pip install --extra-index-url {INDEX_URL} "vtk=={NIGHTLY}"'


def check(demo, minimum, reason, file=None):
    """Print a warning on stderr if VTK is older than ``minimum``.

    Return ``True`` when the installed VTK is recent enough.
    """
    version = installed()
    if version >= minimum:
        return True
    print(
        f"warning: {demo} needs VTK {'.'.join(map(str, minimum))} or newer: "
        f"{reason}.\n"
        f"         Found VTK {'.'.join(map(str, version))}. "
        f"Install a nightly with:\n"
        f"         {install_command()}",
        file=file or sys.stderr,
    )
    return False
