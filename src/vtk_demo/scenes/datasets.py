"""Example datasets, read with VTK from PyVista's data repository.

Files are downloaded on first use and cached in ``$VTK_DEMO_DATA``, by
default ``~/.cache/vtk-demo`` (or ``$XDG_CACHE_HOME/vtk-demo``).
"""

import os
import shutil
import tempfile
import urllib.request
from pathlib import Path

from vtkmodules.vtkImagingCore import vtkImageFlip
from vtkmodules.vtkIOImage import vtkJPEGReader
from vtkmodules.vtkIOPLY import vtkPLYReader
from vtkmodules.vtkIOXML import vtkXMLImageDataReader
from vtkmodules.vtkRenderingCore import vtkTexture

SOURCE = "https://github.com/pyvista/data/raw/master/Data/"


def cache_dir():
    if "VTK_DEMO_DATA" in os.environ:
        return Path(os.environ["VTK_DEMO_DATA"])
    cache = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(cache) / "vtk-demo"


def fetch(filename):
    """Local path of ``filename``, downloaded from :data:`SOURCE` if needed."""
    path = cache_dir() / filename
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with (
            urllib.request.urlopen(SOURCE + filename) as response,
            tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as file,
        ):
            shutil.copyfileobj(response, file)
        Path(file.name).replace(path)  # atomic: no partial file on failure
    return path


def bunny():
    """The Stanford bunny, as a ``vtkPolyData``."""
    return vtkPLYReader(file_name=str(fetch("bunny.ply")))()


def lucy():
    """The Lucy angel statue (Stanford), as a ``vtkPolyData``."""
    return vtkPLYReader(file_name=str(fetch("lucy.ply")))()


def head():
    """A CT scan of a head, as a ``vtkImageData``."""
    return vtkXMLImageDataReader(file_name=str(fetch("head.vti")))()


def sky_box():
    """A sky box, as a mipmapped cube map ``vtkTexture``."""
    texture = vtkTexture(cube_map=True, mipmap=True, interpolate=True)
    texture.SetColorModeToDirectScalars()
    for i, face in enumerate(["posx", "negx", "posy", "negy", "posz", "negz"]):
        image = vtkJPEGReader(file_name=str(fetch(f"skybox2-{face}.jpg")))()
        flip = vtkImageFlip(filtered_axis=1)  # textures start from the bottom row
        flip.SetInputData(image)
        flip.Update()
        texture.SetInputDataObject(i, flip.GetOutput())  # port 1 is a stencil
    return texture
