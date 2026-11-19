"""NRRD volumes, read with numpy into a ``vtkImageData``.

Handles 3D scalar NRRD files with attached data, raw or gzip encoded, as
written by 3D Slicer, including the ones inside its scene bundles (``.mrb``)
which are read in memory, without extracting them.
"""

import gzip
import zipfile
from pathlib import Path

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonDataModel import vtkImageData

_NRRD_TYPES = {
    "signed char": "i1",
    "int8": "i1",
    "uchar": "u1",
    "unsigned char": "u1",
    "uint8": "u1",
    "short": "i2",
    "int16": "i2",
    "ushort": "u2",
    "unsigned short": "u2",
    "uint16": "u2",
    "int": "i4",
    "int32": "i4",
    "uint": "u4",
    "unsigned int": "u4",
    "uint32": "u4",
    "float": "f4",
    "double": "f8",
}


def _vector(text):
    return [float(v) for v in text.strip().strip("()").split(",")]


def read_nrrd(content):
    """A 3D scalar NRRD file (raw or gzip encoded, attached data), as a ``vtkImageData``."""
    header, _, payload = content.partition(b"\n\n")
    fields = {}
    for line in header.decode("latin-1").splitlines()[1:]:
        if line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.lstrip("=").strip()
    if int(fields["dimension"]) != 3:
        msg = f"Only 3D NRRD files are supported, not {fields['dimension']}D"
        raise ValueError(msg)
    sizes = [int(v) for v in fields["sizes"].split()]
    encoding = fields.get("encoding", "raw")
    if encoding in ("gzip", "gz"):
        payload = gzip.decompress(payload)
    elif encoding != "raw":
        msg = f"Unsupported NRRD encoding {encoding!r}"
        raise ValueError(msg)
    endian = "<" if fields.get("endian", "little") == "little" else ">"
    values = np.frombuffer(payload, dtype=endian + _NRRD_TYPES[fields["type"]])
    if values.dtype.kind == "i" and values.min() >= -32768 and values.max() < 32768:
        values = values.astype(np.int16)  # CT fits: half the memory to send

    if "space directions" in fields:
        directions = np.array(
            [_vector(d) for d in fields["space directions"].split(")")[:3]]
        )
        origin = _vector(fields.get("space origin", "(0,0,0)"))
    else:  # old style NRRD: axis aligned, no world space
        directions = np.diag(
            [float(v) for v in fields.get("spacings", "1 1 1").split()]
        )
        origin = [float(v) for v in fields.get("axis mins", "0 0 0").split()]
    if np.linalg.det(directions) < 0:
        # A mirrored orientation, which the GPU volume ray caster renders as
        # noise: store the i axis backward instead, same voxels in space.
        values = values.reshape(sizes[::-1])[:, :, ::-1].ravel()
        origin = np.asarray(origin) + (sizes[0] - 1) * directions[0]
        directions[0] = -directions[0]
    spacing = np.linalg.norm(directions, axis=1)
    image = vtkImageData(dimensions=sizes, spacing=spacing, origin=origin)
    image.SetDirectionMatrix((directions / spacing[:, None]).T.ravel())
    scalars = numpy_to_vtk(np.ascontiguousarray(values), deep=True)
    scalars.SetName("ImageScalars")
    image.point_data.SetScalars(scalars)
    return image


def read_mrb_volume(path):
    """The main volume of a 3D Slicer scene bundle (``.mrb``), read in memory.

    That is the largest 3D scalar NRRD of the bundle: label maps compress
    much better than images, and segmentations (``.seg.nrrd``) or 4D volumes
    (diffusion, sequences) are skipped.
    """
    with zipfile.ZipFile(path) as bundle:
        members = sorted(
            (
                info
                for info in bundle.infolist()
                if info.filename.endswith(".nrrd")
                and not info.filename.endswith(".seg.nrrd")
            ),
            key=lambda info: info.file_size,
            reverse=True,
        )
        for info in members:
            try:
                return read_nrrd(bundle.read(info))
            except (ValueError, KeyError):
                continue
    msg = f"No 3D scalar NRRD volume in {path}"
    raise ValueError(msg)


def read_volume(path):
    """A 3D scalar volume from a NRRD file or a 3D Slicer scene bundle (``.mrb``)."""
    path = Path(path)
    if path.suffix == ".mrb":
        return read_mrb_volume(path)
    return read_nrrd(path.read_bytes())
