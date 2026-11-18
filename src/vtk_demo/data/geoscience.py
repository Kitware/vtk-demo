"""Terrain, geophysics and global earth models."""

from .core import DataSet, License, MetaData
from .sources import pyvista

PVGEO = "PVGeo / PyVista contributors (Bane Sullivan)"

DAMAVAND = DataSet(
    name="damavand",
    location=pyvista(
        "AOI.Damavand.32639.vtp",
        "a6c4f242d3c7a4ab6c5eb37f3da376474f6e0e56e978745373d540502a972e09",
        5881015,
    ),
    metadata=MetaData(
        author=PVGEO,
        license=License.UNKNOWN,
        description="Topography around Mount Damavand, Iran (UTM 39N), with elevation.",
        tags={"geoscience", "terrain", "polydata", "vtp"},
    ),
)

RUAPEHU = DataSet(
    name="ruapehu",
    location=pyvista(
        "Ruapehu_mag_dem_15m_NZTM.vtk",
        "1d8d85c97cccf598e85a29169ba8eb58b3187be230be4ed9e1e17451d2358d84",
        13440250,
    ),
    metadata=MetaData(
        author=PVGEO,
        license=License.UNKNOWN,
        description="15m elevation and magnetic grid of Mount Ruapehu, New Zealand.",
        tags={"geoscience", "terrain", "image", "vtk"},
    ),
)

SIO = DataSet(
    name="sio020320",
    location=pyvista(
        "Sio020320.vtp",
        "eb4df0c0e1925f972023f798d81fd778027985ad9c25a2c57b49242fbeb74b16",
        7674906,
    ),
    metadata=MetaData(
        author=PVGEO,
        license=License.UNKNOWN,
        description="Geoscience surface mesh from the PVGeo sample data.",
        tags={"geoscience", "terrain", "polydata", "vtp"},
    ),
)

ANTARCTICA_VELOCITY = DataSet(
    name="antarctica-velocity",
    location=pyvista(
        "antarctica_velocity.vtp",
        "675f5ab69eb387ae7398d187d2ffbf4509414c3935c5a6878c499096a53998f2",
        33435218,
    ),
    metadata=MetaData(
        author=PVGEO,
        license=License.UNKNOWN,
        description="Ice sheet flow velocity over Antarctica (ssavelocity vectors).",
        tags={"geoscience", "glaciology", "polydata", "vector", "vtp"},
    ),
)

KAFADAR_LIDAR = DataSet(
    name="kafadar-lidar",
    location=pyvista(
        "kafadar-lidar-interp.vtp",
        "1e3ed11ad976866302287d289c3058c4d2417d791079c4b1a7a60f27a8353849",
        37814187,
    ),
    metadata=MetaData(
        author=PVGEO,
        license=License.UNKNOWN,
        description="LiDAR point cloud (3.4M points) with elevation.",
        tags={"geoscience", "lidar", "point-cloud", "polydata", "vtp"},
    ),
)

GPR_LINE = DataSet(
    name="gpr-line",
    location=pyvista(
        "gpr-line.vtu",
        "8881c8633b21d65d31862c191d06466c34480534f04f843ce7fe9c2aed68899c",
        6526184,
    ),
    metadata=MetaData(
        author=PVGEO,
        license=License.UNKNOWN,
        description="Ground penetrating radar section along a survey line.",
        tags={"geoscience", "geophysics", "unstructured", "vtu"},
    ),
)

TOPOGRAPHY = DataSet(
    name="etopo",
    location=pyvista(
        "EarthModels/ETOPO_10min_Ice.vtp",
        "89fff96333d351ad207bce0599c8a1df011853be8aaaa6face1f0c472d6676bf",
        45156388,
    ),
    metadata=MetaData(
        author=PVGEO,
        license=License.UNKNOWN,
        description="ETOPO global relief at 10 arc-minutes (ice surface), on a sphere.",
        tags={"geoscience", "earth", "terrain", "polydata", "vtp"},
    ),
)

TOPOGRAPHY_LAND = DataSet(
    name="etopo-land",
    location=pyvista(
        "EarthModels/ETOPO_10min_Ice_only-land.vtp",
        "e59b77278a9c0449d6350ab1604da913aad9bff0440635091e5a782f15818cf3",
        15225532,
    ),
    metadata=MetaData(
        author=PVGEO,
        license=License.UNKNOWN,
        description="ETOPO global relief at 10 arc-minutes, land only.",
        tags={"geoscience", "earth", "terrain", "polydata", "vtp"},
    ),
)

COASTLINES = DataSet(
    name="coastlines",
    location=pyvista(
        "EarthModels/Coastlines_Los_Alamos.vtp",
        "5bd3bbfff7de4e0bb56aec84a4d77a35b84e05f27232c3af5f0e2c4c7f635aa1",
        221145,
    ),
    metadata=MetaData(
        author=PVGEO,
        license=License.UNKNOWN,
        description="Global coastlines (from Los Alamos), as lines on a sphere.",
        tags={"geoscience", "earth", "polydata", "lines", "vtp"},
    ),
)
