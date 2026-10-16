# Contributing to vtk-demo

## Development setup

With [uv](https://docs.astral.sh/uv/), set up a `.venv` with every extra and
the development dependencies (for your editor, or to run the demos from the
checkout):

```bash
uv sync --all-extras --dev
uv run vtk-demo list
```

Lint, tests and builds go through [nox](https://nox.thea.codes/) (the same
sessions run in CI):

```bash
uvx nox                   # lint + tests on Python 3.10 to 3.13
uvx nox -s tests-3.12     # a single Python version
uvx nox -s tests-3.12 -- -k galaxy   # extra arguments are passed to pytest
uvx nox -s format         # ruff --fix and ruff format
uvx nox -s build          # sdist + wheel in dist/, smoke tested
```

## Adding a demo

1. Build the scene in `vtk_demo/scenes/` as a `build_*(renderer, ...)` function,
   in plain VTK (no PyVista).
2. Add `vtk_demo/apps/<group>/<name>.py` with a `main()` reading `sys.argv`.
3. Register it in `DEMOS` (`vtk_demo/apps/__init__.py`).
4. Add a 1280×800 screenshot to `docs/screenshots/` and to the gallery in the [README](README.md#gallery).

## Releasing

Commits on `main` follow [Conventional Commits](https://www.conventionalcommits.org/)
(`fix:` → patch, `feat:` → minor, `feat!:` / `BREAKING CHANGE:` → major;
`major_on_zero = false` keeps breaking changes on the minor while in `0.x`).

Releases are manual: **Actions › Release › Run workflow** on `main`. The workflow
runs the tests, then [python-semantic-release](https://python-semantic-release.readthedocs.io/)
bumps `__version__`, updates `CHANGELOG.md`, commits, tags `vX.Y.Z` and creates
the GitHub release. The wheel and sdist built with `uvx nox -s build` are attached to
the release and published to PyPI. Use `dry_run` to preview the next version,
or `force` to pick the bump yourself.

Preview locally with:

```bash
uvx --from python-semantic-release semantic-release --noop version --print
```
