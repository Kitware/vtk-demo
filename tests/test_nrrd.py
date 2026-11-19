import gzip
import zipfile

import numpy as np
import pytest

from vtk_demo.data import medical
from vtk_demo.io.nrrd import read_mrb_volume, read_nrrd, read_volume


def _header(header):
    lines = "".join(f"{k}: {v}\n" for k, v in header.items())
    return f"NRRD0004\n{lines}\n".encode()


def _nrrd(values, header):
    return _header(header) + gzip.compress(values.tobytes())


def _space_nrrd(values):
    nz, ny, nx = values.shape
    return _nrrd(
        values,
        {
            "type": "short",
            "dimension": 3,
            "space": "left-posterior-superior",
            "sizes": f"{nx} {ny} {nz}",
            "space directions": "(0.5,0,0) (0,0.5,0) (0,0,2)",
            "endian": "little",
            "encoding": "gzip",
            "space origin": "(1,2,3)",
        },
    )


def test_read_nrrd_space():
    values = np.arange(24, dtype="<i2").reshape(2, 3, 4)
    image = read_nrrd(_space_nrrd(values))
    assert image.GetDimensions() == (4, 3, 2)
    assert image.GetSpacing() == (0.5, 0.5, 2)
    assert image.GetOrigin() == (1, 2, 3)
    assert image.point_data.GetScalars().GetRange() == (0, 23)


def test_read_nrrd_old_style():
    values = np.arange(8, dtype=np.uint8).reshape(2, 2, 2)
    header = {
        "type": "unsigned char",
        "dimension": 3,
        "sizes": "2 2 2",
        "spacings": "0.625 0.625 2.5",
        "axis mins": "-1 -2 3",
        "encoding": "gzip",
    }
    image = read_nrrd(_nrrd(values, header))
    assert image.GetSpacing() == (0.625, 0.625, 2.5)
    assert image.GetOrigin() == (-1, -2, 3)


def test_read_nrrd_4d():
    header = {"type": "short", "dimension": 4, "sizes": "1 2 2 2"}
    with pytest.raises(ValueError, match="3D"):
        read_nrrd(_nrrd(np.zeros(8, np.int16), header))


def test_read_mrb_largest_volume(tmp_path):
    image = np.random.default_rng(0).integers(-1000, 1000, (8, 8, 8)).astype("<i2")
    label = np.zeros((8, 8, 8), "<i2")
    four_d = {"type": "short", "dimension": 4, "sizes": "9 8 8 8", "encoding": "raw"}
    path = tmp_path / "scene.mrb"
    with zipfile.ZipFile(path, "w") as bundle:
        bundle.writestr("scene/Data/label.nrrd", _space_nrrd(label))
        bundle.writestr("scene/Data/image.nrrd", _space_nrrd(image))
        bundle.writestr("scene/Data/dwi.nrrd", _header(four_d) + bytes(9 * 512 * 2))
        bundle.writestr("scene/Data/big.seg.nrrd", b"x" * 99999)
    volume = read_mrb_volume(path)
    assert volume.point_data.GetScalars().GetRange() == (image.min(), image.max())
    assert read_volume(path).GetDimensions() == (8, 8, 8)


def test_read_volume_nrrd(tmp_path):
    path = tmp_path / "image.nrrd"
    path.write_bytes(_space_nrrd(np.zeros((2, 3, 4), "<i2")))
    assert read_volume(path).GetDimensions() == (4, 3, 2)


def test_scalar_volumes():
    names = medical.scalar_volumes()
    assert "ct-chest-scene" in names
    assert "mr-head-scene" in names
    assert "lge-mri" in names
    for excluded in ("ct-cardio-seq", "dwi-volume-scene", "left-atrium-endo"):
        assert excluded not in names
    assert "ct-cardio-multivolume" not in names  # zip archive


def test_read_nrrd_mirrored_orientation():
    """A left-handed orientation is made right-handed, voxels staying in place."""
    nx, ny, nz = 4, 3, 2
    values = np.arange(nx * ny * nz, dtype="<f4").reshape(nz, ny, nx)
    directions = np.array([(0, 0.75, 0), (0, 0, -0.75), (0.75, 0, 0)])  # det < 0
    origin = np.array([-77.625, -107.625, 119.625])
    header = {
        "type": "float",
        "dimension": 3,
        "sizes": f"{nx} {ny} {nz}",
        "space directions": " ".join(f"({a},{b},{c})" for a, b, c in directions),
        "endian": "little",
        "encoding": "gzip",
        "space origin": "({},{},{})".format(*origin),
    }
    image = read_nrrd(_nrrd(values, header))
    matrix = np.array(
        [
            image.GetDirectionMatrix().GetElement(r, c)
            for r in range(3)
            for c in range(3)
        ]
    )
    assert np.linalg.det(matrix.reshape(3, 3)) > 0
    scalars = image.point_data.GetScalars()
    for k, j, i in np.ndindex(nz, ny, nx):
        expected = origin + i * directions[0] + j * directions[1] + k * directions[2]
        point_id = image.FindPoint(expected)
        assert scalars.GetValue(point_id) == values[k, j, i]
        assert np.allclose(image.GetPoint(point_id), expected)
