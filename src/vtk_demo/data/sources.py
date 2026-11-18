"""Remote repositories datasets are downloaded from."""

from pathlib import PurePosixPath

from .core import RemoteLocation

# Pinned to a commit so the sha256 of every file stays valid
PYVISTA_DATA_COMMIT = "5a3de12d34c24aa5dd5e5db1cbc2defebc0d4da3"
PYVISTA_DATA = (
    f"https://raw.githubusercontent.com/pyvista/data/{PYVISTA_DATA_COMMIT}/Data"
)
PYVISTA_DATA_REPO = "https://github.com/pyvista/data"


def pyvista(path: str, sha256: str, size: int, uncompress: bool = False):
    """A file of https://github.com/pyvista/data, cached in ``pyvista/<path>``."""
    return RemoteLocation(
        url=f"{PYVISTA_DATA}/{path}",
        known_hash=f"sha256:{sha256}",
        uncompress=uncompress,
        fname=f"pyvista/{path}",
        size=size,
    )


def google_drive_url(file_id: str) -> str:
    """Direct download URL of a public Google Drive file (no virus-scan page)."""
    return (
        "https://drive.usercontent.google.com/download"
        f"?id={file_id}&export=download&confirm=t"
    )


# Pinned to a commit so the sha256 of every file stays valid
DEEP_TRANSPARENCY_COMMIT = "a11f505d9101f2ecff54c726f2b4ade2cd5c4e7c"
DEEP_TRANSPARENCY_DATA = (
    "https://raw.githubusercontent.com/PaulHax/vtk-js-deep-transparency/"
    f"{DEEP_TRANSPARENCY_COMMIT}/Data/deep-transparency"
)
DEEP_TRANSPARENCY_REPO = (
    "https://github.com/PaulHax/vtk-js-deep-transparency/tree/"
    f"{DEEP_TRANSPARENCY_COMMIT}/Data/deep-transparency"
)


def deep_transparency(path: str, sha256: str, size: int, folder: str):
    """A file of the vtk-js-deep-transparency gallery data.

    Cached in ``deep-transparency/<folder>/<file name>``.
    """
    return RemoteLocation(
        url=f"{DEEP_TRANSPARENCY_DATA}/{path}",
        known_hash=f"sha256:{sha256}",
        fname=f"deep-transparency/{folder}/{PurePosixPath(path).name}",
        size=size,
    )


SLICER_DATA_STORE = "https://github.com/Slicer/SlicerDataStore/releases/tag/SHA256"
SLICER_DATA_STORE_URL = (
    "https://github.com/Slicer/SlicerDataStore/releases/download/SHA256"
)


def slicer(file_name: str, sha256: str, size: int):
    """A file of the SlicerDataStore SHA256 release, cached in ``slicer/<file_name>``.

    Release assets are named after their sha256, so ``file_name`` (with its
    extension) is the name the file had when uploaded.
    """
    return RemoteLocation(
        url=f"{SLICER_DATA_STORE_URL}/{sha256}",
        known_hash=f"sha256:{sha256}",
        fname=f"slicer/{file_name}",
        size=size,
    )
