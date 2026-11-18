"""Core types of the dataset registry.

A :class:`DataSet` is made of one or more :class:`RemoteLocation` that pooch
downloads (and optionally uncompresses) on first use. Files are cached in
``$VTK_DEMO_DATA``, by default ``~/.cache/vtk-demo`` (or
``$XDG_CACHE_HOME/vtk-demo``), and checked against their sha256 on download.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import tarfile
import threading
from collections.abc import Generator, Iterable, Sequence
from collections.abc import Set as AbstractSet
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

import pooch

# Background downloads of DataSet.available
_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="vtk-demo-data")


def cache_dir() -> Path:
    """Root directory where datasets are downloaded."""
    if "VTK_DEMO_DATA" in os.environ:
        return Path(os.environ["VTK_DEMO_DATA"])
    cache = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(cache) / "vtk-demo"


class License(Enum):
    """License of a dataset, valued by its SPDX identifier."""

    BSD = "BSD-3-Clause"
    MIT = "MIT"
    Apache = "Apache-2.0"
    CC0 = "CC0-1.0"
    CC_BY_4 = "CC-BY-4.0"
    CC_BY_SA_2_5 = "CC-BY-SA-2.5"
    CC_BY_NC_4 = "CC-BY-NC-4.0"
    CC_BY_NC_SA_4 = "CC-BY-NC-SA-4.0"
    PUBLIC_DOMAIN = "LicenseRef-PublicDomain"
    STANFORD = "LicenseRef-StanfordScanningRepository"
    SIMSCALE = "LicenseRef-SimScale"
    UNKNOWN = "LicenseRef-unknown"

    @property
    def commercial_use(self) -> bool:
        """Whether the license is known to allow commercial use."""
        return self not in _NON_COMMERCIAL


_NON_COMMERCIAL = {
    License.CC_BY_NC_4,
    License.CC_BY_NC_SA_4,
    License.STANFORD,  # products for sale need Stanford's permission
    License.UNKNOWN,
}


@dataclass(frozen=True)
class MetaData:
    author: str
    license: License
    description: str = ""
    tags: AbstractSet[str] = frozenset()  # stored as a frozenset
    reference: str | None = None  # URL of the original source

    def __post_init__(self):
        object.__setattr__(self, "tags", frozenset(self.tags))


_ARCHIVES = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")
_COMPRESSED = (".gz", ".bz2", ".xz")


# One lock per downloaded file, so datasets sharing an archive fetch it once
_DOWNLOAD_LOCKS: dict[Path, threading.Lock] = {}
_DOWNLOAD_LOCKS_LOCK = threading.Lock()


def _download_lock(path: Path) -> threading.Lock:
    with _DOWNLOAD_LOCKS_LOCK:
        return _DOWNLOAD_LOCKS.setdefault(path, threading.Lock())


@dataclass(frozen=True)
class RemoteLocation:
    """A remote file, stored at ``cache_dir() / fname`` once downloaded.

    With ``uncompress``, archives (``.zip``, ``.tar.*``) are extracted in a
    directory named after the archive without its extension, and compressed
    files (``.gz``, ``.bz2``, ``.xz``) are decompressed next to the download.
    """

    url: str
    known_hash: str | None = None
    uncompress: bool = False
    fname: str | None = None  # relative path in the cache, default to url name
    size: int | None = None  # in bytes, for UIs to show before downloading

    def __post_init__(self):
        if self.uncompress and not self.name.endswith(_ARCHIVES + _COMPRESSED):
            msg = f"Don't know how to uncompress {self.url}"
            raise ValueError(msg)

    @property
    def name(self) -> str:
        return self.fname or PurePosixPath(urlparse(self.url).path).name

    @property
    def is_archive(self) -> bool:
        return self.uncompress and self.name.endswith(_ARCHIVES)

    def download_path(self, root: Path) -> Path:
        return root / self.name

    def output_path(self, root: Path) -> Path:
        """Local path once downloaded and uncompressed."""
        path = self.download_path(root)
        if not self.uncompress:
            return path
        for ext in _ARCHIVES + _COMPRESSED:
            if path.name.endswith(ext):
                return path.with_name(path.name[: -len(ext)])
        return path

    def retrieve(self, root: Path) -> Path:
        """Download (if needed) and return :meth:`output_path`."""
        download = self.download_path(root)
        output = self.output_path(root)
        processor = None
        if self.is_archive:
            unpack = pooch.Unzip if download.name.endswith(".zip") else pooch.Untar
            processor = unpack(extract_dir=output.name)
        elif self.uncompress:
            processor = pooch.Decompress(name=output.name)
        with _download_lock(download):
            pooch.retrieve(
                self.url,
                known_hash=self.known_hash,
                fname=download.name,
                path=download.parent,
                processor=processor,
            )
        return output


@dataclass(frozen=True)
class ArchiveMember(RemoteLocation):
    """A tar archive ``member`` of the remote tar archive at ``url``.

    The outer archive is downloaded once (and kept, shared by every member),
    then ``member`` alone is streamed out of it and extracted in a directory
    named after it without its extension, next to the outer archive.
    """

    member: str = ""

    def __post_init__(self):
        super().__post_init__()
        if not self.member.endswith(_ARCHIVES) or self.member.endswith(".zip"):
            msg = f"Member {self.member!r} of {self.url} must be a tar archive"
            raise ValueError(msg)

    @property
    def is_archive(self) -> bool:
        return True

    def output_path(self, root: Path) -> Path:
        name = PurePosixPath(self.member).name
        for ext in _ARCHIVES:
            if name.endswith(ext):
                name = name[: -len(ext)]
                break
        return self.download_path(root).parent / name

    def retrieve(self, root: Path) -> Path:
        download = self.download_path(root)
        output = self.output_path(root)
        with _download_lock(download):
            pooch.retrieve(
                self.url,
                known_hash=self.known_hash,
                fname=download.name,
                path=download.parent,
            )
            if not output.exists():
                self._extract(download, output)
        return output

    def _extract(self, download: Path, output: Path):
        partial = output.with_name(f"{output.name}.partial")
        shutil.rmtree(partial, ignore_errors=True)
        with tarfile.open(download, "r|*") as outer:
            for info in outer:
                if info.name == self.member:
                    with tarfile.open(
                        fileobj=outer.extractfile(info), mode="r|*"
                    ) as inner:
                        _extract_all(inner, partial)
                    break
            else:
                msg = f"No {self.member!r} in {download}"
                raise KeyError(msg)
        partial.rename(output)


def _extract_all(archive: tarfile.TarFile, path: Path):
    if hasattr(tarfile, "data_filter"):  # Python 3.10.12+
        archive.extractall(path, filter="data")
    else:
        archive.extractall(path)  # noqa: S202


class DataSet:
    """A named dataset, registered in :attr:`AVAILABLE_DATASETS` on creation.

    :attr:`path` is the file (or directory) to hand to a reader. It is
    ``entry`` relative to the first location (its extraction directory for an
    archive, its parent directory otherwise), or the first location itself
    when ``entry`` is not given.
    """

    AVAILABLE_DATASETS: dict[str, DataSet] = {}

    def __init__(
        self,
        name: str,
        location: RemoteLocation | Sequence[RemoteLocation],
        metadata: MetaData,
        entry: str | None = None,
    ):
        self.name = name
        self.locations = (
            (location,) if isinstance(location, RemoteLocation) else tuple(location)
        )
        if not self.locations:
            msg = f"Dataset {name!r} needs at least one location"
            raise ValueError(msg)
        self.meta = metadata
        self.entry = entry
        self._lock = threading.Lock()  # one download at a time
        self._future_lock = threading.Lock()
        self._future: Future[Path] | None = None

        # Register ourself
        self.register_dataset(self)

    def __repr__(self):
        return f"DataSet({self.name!r})"

    @property
    def tags(self) -> AbstractSet[str]:
        return self.meta.tags

    @property
    def usage(self) -> str:
        """Dataset, author, license and origin, to credit it properly."""
        meta = self.meta
        license = meta.license.value
        if not meta.license.commercial_use:
            license += " (non-commercial use only, or check with the author)"
        lines = [
            f"Dataset:     {self.name}",
            f"Description: {meta.description}",
            f"Author:      {meta.author}",
            f"License:     {license}",
        ]
        if meta.reference:
            lines.append(f"Reference:   {meta.reference}")
        urls = [loc.url for loc in self.locations]
        lines.append(f"Source:      {urls[0]}")
        lines.extend(f"             {url}" for url in urls[1:])
        return "\n".join(lines)

    def print_usage(self, file=None):
        """Print :attr:`usage`: what to credit when using this dataset."""
        print(self.usage, file=file)

    @property
    def size(self) -> int | None:
        """Download size in bytes, if known for every location."""
        total = 0
        for loc in self.locations:
            if loc.size is None:
                return None
            total += loc.size
        return total

    @property
    def files(self) -> list[Path]:
        """Local paths of every location, once downloaded."""
        root = cache_dir()
        return [loc.output_path(root) for loc in self.locations]

    @property
    def is_local(self) -> bool:
        """Whether every file is already downloaded (no hash check)."""
        return all(f.exists() for f in self.files)

    def _download(self) -> Path:
        """Download every missing file (blocking) and return :attr:`path`."""
        with self._lock:
            root = cache_dir()
            for loc in self.locations:
                loc.retrieve(root)
        return self._path()

    def _download_in_background(self) -> Future[Path]:
        """The in-flight background download, started if needed."""
        with self._future_lock:
            if self._future is None:
                self._future = _EXECUTOR.submit(self._download)
            return self._future

    @property
    def available(self) -> Available:
        """Await it to have every file on disk, so :attr:`path` won't block.

            ds = data.get("head")
            await ds.available
            reader.file_name = ds.path

        Nothing starts until awaited. Awaiting also returns :attr:`path`.
        """
        return Available(self)

    async def _fetch(self) -> Path:
        """Download every missing file without blocking the event loop."""
        if self._future is None and self.is_local:
            return self._path()
        future = self._download_in_background()
        try:
            return await asyncio.wrap_future(future)
        finally:
            self._forget(future)

    def _forget(self, future: Future[Path]):
        """Drop a finished download, so a failed one can be retried."""
        with self._future_lock:
            if self._future is future and future.done():
                self._future = None

    @property
    def path(self) -> Path:
        """Local path to read, downloaded first if needed (blocking)."""
        if not self.is_local:
            return self._download()
        return self._path()

    def _path(self) -> Path:
        first = self.locations[0]
        output = first.output_path(cache_dir())
        if self.entry is None:
            return output
        base = output if first.is_archive else output.parent
        return base / self.entry

    @classmethod
    def get(cls, name: str) -> DataSet:
        return cls.AVAILABLE_DATASETS[name]

    @classmethod
    def list_datasets(cls, tags: Iterable[str] | None = None) -> Iterable[DataSet]:
        """Every dataset, or the ones with at least one of ``tags``."""
        if not tags:
            return cls.AVAILABLE_DATASETS.values()

        filters = set(tags)
        return (
            ds
            for ds in cls.AVAILABLE_DATASETS.values()
            if not ds.tags.isdisjoint(filters)
        )

    @classmethod
    def register_dataset(cls, ds: DataSet):
        if ds.name in cls.AVAILABLE_DATASETS:
            msg = f"A dataset named {ds.name!r} is already registered"
            raise ValueError(msg)
        cls.AVAILABLE_DATASETS[ds.name] = ds


class Available:
    """Awaitable returned by :attr:`DataSet.available`.

    Lazy: the download (if needed) starts when awaited, not on creation.
    """

    __slots__ = ("dataset",)

    def __init__(self, dataset: DataSet):
        self.dataset = dataset

    def __await__(self) -> Generator[Any, None, Path]:
        return self.dataset._fetch().__await__()

    def __repr__(self):
        return f"<{self.dataset.name} available={self.dataset.is_local}>"


def print_usage(*datasets: DataSet) -> None:
    """Print the usage (author, license, origin) of every dataset in a banner."""
    print()
    print("=" * 80)
    print(f"Using dataset{'s' if len(datasets) > 1 else ''}:")
    print("=" * 80)
    for ds in datasets:
        ds.print_usage()
        print("=" * 80)
    print()
