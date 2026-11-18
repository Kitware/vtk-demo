"""NRRD volumes, read with numpy into a ``vtkImageData``.

Handles 3D scalar NRRD files with attached data, raw or gzip encoded, as
written by 3D Slicer, including the ones inside its scene bundles (``.mrb``)
which are read in memory, without extracting them.
"""

import gzip
import zipfile

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

    directions = np.array(
        [_vector(d) for d in fields["space directions"].split(")")[:3]]
    )
    spacing = np.linalg.norm(directions, axis=1)
    image = vtkImageData(
        dimensions=sizes,
        spacing=spacing,
        origin=_vector(fields.get("space origin", "(0,0,0)")),
    )
    image.SetDirectionMatrix((directions / spacing[:, None]).T.ravel())
    scalars = numpy_to_vtk(np.ascontiguousarray(values), deep=True)
    scalars.SetName("ImageScalars")
    image.point_data.SetScalars(scalars)
    return image


def read_mrb_volume(path):
    """The first NRRD volume of a 3D Slicer scene bundle (``.mrb``), read in memory."""
    with zipfile.ZipFile(path) as bundle:
        name = next(n for n in bundle.namelist() if n.endswith(".nrrd"))
        return read_nrrd(bundle.read(name))
