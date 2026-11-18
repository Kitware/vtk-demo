import io

from vtk_demo import vtk_version


def test_recent_enough(monkeypatch):
    monkeypatch.setattr(vtk_version, "installed", lambda: (9, 7, 20261101))
    out = io.StringIO()
    assert vtk_version.check("demo", vtk_version.WEBGPU_DEEP_FRAMEBUFFER, "x", out)
    assert out.getvalue() == ""


def test_too_old_warns_with_install_command(monkeypatch):
    monkeypatch.setattr(vtk_version, "installed", lambda: (9, 7, 1))
    out = io.StringIO()
    assert not vtk_version.check(
        "trame.animation", vtk_version.VTK_WASM_ARRAY_UPDATES, "reason", out
    )
    message = out.getvalue()
    assert "trame.animation needs VTK 9.7.2 or newer: reason" in message
    assert "Found VTK 9.7.1" in message
    assert vtk_version.install_command() in message


def test_next_minor_release_is_recent_enough(monkeypatch):
    monkeypatch.setattr(vtk_version, "installed", lambda: (9, 8, 0))
    assert vtk_version.check(
        "demo", vtk_version.WEBGPU_DEEP_FRAMEBUFFER, "x", io.StringIO()
    )


def test_installed_vtk():
    major, minor, _ = vtk_version.installed()
    assert (major, minor) >= (9, 7)


def test_nightly_matches_uv_pin():
    from pathlib import Path

    pyproject = Path(__file__).parents[1] / "pyproject.toml"
    assert f'"vtk=={vtk_version.NIGHTLY}"' in pyproject.read_text()
