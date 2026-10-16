"""``vtk-demo``: list and launch the bundled demos.

vtk-demo list
vtk-demo run trame.glyph --webgpu
vtk-demo run glyph --help          # the group can be omitted
"""

import argparse
import importlib
import sys

from .apps import DEMOS, GROUPS, find


def list_demos():
    visible = [d for d in DEMOS if not d.hidden]
    width = max(len(d.id) for d in visible)
    for group, description in GROUPS.items():
        print(f"{group}: {description}")
        demos = [d for d in visible if d.group == group]
        for demo in demos:
            print(f"  {demo.id:<{width}}  {demo.summary}")
        if not demos:
            print("  (none yet)")
        print()


def run_demo(demo_id, args):
    try:
        demo = find(demo_id)
    except KeyError as e:
        sys.exit(f"error: {e.args[0]}")
    try:
        module = importlib.import_module(demo.module)
    except ModuleNotFoundError as e:
        if (e.name or "").startswith("vtk_demo"):
            raise
        sys.exit(
            f"error: {demo.id} needs extra dependencies ({e}).\n"
            f'Install them with: pip install "vtk-demo[{demo.group}]"'
        )
    # Demos read their options from sys.argv
    sys.argv = [f"vtk-demo run {demo.id}", *args]
    return module.main()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="vtk-demo", description="Demos that show off VTK capabilities"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List the available demos")
    run = commands.add_parser(
        "run", help="Run a demo; extra arguments are passed to it"
    )
    run.add_argument("demo", help="Demo id, e.g. trame.glyph")
    run.add_argument("args", nargs=argparse.REMAINDER, help="Demo arguments")

    args = parser.parse_args(argv)
    if args.command == "list":
        list_demos()
    else:
        run_demo(args.demo, args.args)


if __name__ == "__main__":
    main()
