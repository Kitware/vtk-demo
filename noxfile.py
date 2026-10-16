# /// script
# dependencies = ["nox>=2025.2.9"]
# ///
"""Development tasks, run with ``uvx nox`` (``uvx nox -l`` lists the sessions).

Every session syncs its virtualenv from ``uv.lock``, so local runs and CI use
the exact same dependencies (including the VTK nightly constraint).
"""

from __future__ import annotations

import glob

import nox

nox.needs_version = ">=2025.2.9"
nox.options.default_venv_backend = "uv"
nox.options.sessions = ["lint", "tests"]

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]


def uv_sync(session: nox.Session, *args: str) -> None:
    """Install the locked dependencies into the session virtualenv."""
    session.run_install(
        "uv",
        "sync",
        "--locked",
        *args,
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )


@nox.session
def lint(session: nox.Session) -> None:
    """Check linting and formatting with ruff."""
    uv_sync(session, "--only-group", "dev")
    session.run("ruff", "check", ".")
    session.run("ruff", "format", "--check", ".")


@nox.session(name="format", default=False)
def format_(session: nox.Session) -> None:
    """Fix lint issues and reformat the code with ruff."""
    uv_sync(session, "--only-group", "dev")
    session.run("ruff", "check", "--fix", ".")
    session.run("ruff", "format", ".")


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite with all the extras installed."""
    uv_sync(session, "--all-extras")
    session.run("pytest", "-v", *session.posargs)


@nox.session(default=False)
def build(session: nox.Session) -> None:
    """Build the sdist and wheel into dist/, then smoke test the wheel."""
    session.run("uv", "build", "--clear", external=True)
    (wheel,) = glob.glob("dist/*.whl")
    # --no-config: resolve like a user would, without the [tool.uv] constraints
    session.install("--no-config", wheel)
    session.run("vtk-demo", "list")


if __name__ == "__main__":
    nox.main()
