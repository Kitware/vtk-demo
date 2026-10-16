import importlib.util

import pytest

from vtk_demo.apps import DEMOS, GROUPS, find
from vtk_demo.cli import main


def test_demo_modules_exist():
    for demo in DEMOS:
        assert demo.group in GROUPS
        assert importlib.util.find_spec(demo.module) is not None, demo.module


def test_ids_are_unique():
    ids = [d.id for d in DEMOS]
    assert len(ids) == len(set(ids))


def test_find():
    assert find("trame.glyph").name == "glyph"
    assert find("glyph").group == "trame"
    with pytest.raises(KeyError):
        find("nope")


def test_list(capsys):
    main(["list"])
    out = capsys.readouterr().out
    assert "trame.glyph" in out
    assert "imgui:" in out
    assert "actor-world" not in out


def test_hidden_demos_can_be_found():
    assert find("trame.actor-world").hidden
