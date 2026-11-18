"""Pool of sample datasets for 3D visualization, downloaded on demand.

from vtk_demo import data

for ds in data.list_datasets(["medical"]):
    print(ds.name, ds.meta.description)

path = data.get("bunny").path  # blocking download on first use

ds = data.get("head")
await ds.available  # same, without blocking the event loop
path = ds.path
"""

from collections.abc import Iterable

from . import (
    ensembles,
    environments,
    geoscience,
    medical,
    meshes,
    molecules,
    simulations,
    transparency,
    volumes,
)
from .core import (
    ArchiveMember,
    DataSet,
    License,
    MetaData,
    RemoteLocation,
    cache_dir,
    print_usage,
)

__all__ = [
    "ArchiveMember",
    "print_usage",
    "DataSet",
    "License",
    "MetaData",
    "RemoteLocation",
    "cache_dir",
    "ensembles",
    "environments",
    "geoscience",
    "get",
    "list_datasets",
    "list_tags",
    "medical",
    "meshes",
    "molecules",
    "simulations",
    "transparency",
    "volumes",
]


def get(name: str) -> DataSet:
    """The dataset registered as ``name``."""
    return DataSet.get(name)


def list_datasets(tags: Iterable[str] | None = None) -> list[DataSet]:
    """Every dataset, or the ones with at least one of ``tags``."""
    return list(DataSet.list_datasets(tags))


def list_tags() -> list[str]:
    """Every tag used by a registered dataset."""
    return sorted({tag for ds in DataSet.list_datasets() for tag in ds.tags})
