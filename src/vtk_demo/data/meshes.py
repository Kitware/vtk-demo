"""Surface meshes: scanned statues, CAD parts and textured models."""

from .core import DataSet, License, MetaData
from .sources import pyvista

STANFORD = "Stanford Computer Graphics Laboratory"
STANFORD_URL = "http://graphics.stanford.edu/data/3Dscanrep/"
VTK_DATA = "VTKData (git://vtk.org/VTKData.git)"
VTK_EXAMPLES = "VTKExamples (Bill Lorensen)"
VIEWPOINT = "Viewpoint DataLabs International (distributed with permission)"
PYVISTA = "PyVista contributors"
NEFERTITI_AUTHOR = "Nora Al-Badri and Jan Nikolai Nelles, The Other Nefertiti (2016)"
KHRONOS = "Khronos glTF Sample Models"

BUNNY = DataSet(
    name="bunny",
    location=pyvista(
        "Bunny.vtp",
        "aa0b1f7fc5210769ba707af4584b71b92dea365a8a6c71d8d6567c0d0be6d421",
        33381,
    ),
    metadata=MetaData(
        author=STANFORD,
        license=License.STANFORD,
        description="The Stanford bunny (decimated).",
        tags={"mesh", "polydata", "scan", "vtp"},
        reference=STANFORD_URL,
    ),
)

DRAGON = DataSet(
    name="dragon",
    location=pyvista(
        "dragon.ply",
        "fea87ff48f2aba22fb53e7b67c3ff3f7b8c2a3b3a0653af62c48bba67c6d5744",
        33831477,
    ),
    metadata=MetaData(
        author=STANFORD,
        license=License.STANFORD,
        description="The Stanford dragon.",
        tags={"mesh", "polydata", "scan", "ply"},
        reference=STANFORD_URL,
    ),
)

LUCY = DataSet(
    name="lucy",
    location=pyvista(
        "lucy.ply",
        "c57a95174c3c24d87c1ce8b44f48cbf0a5fcab47ce938880ec2acd497a478eb3",
        1899711,
    ),
    metadata=MetaData(
        author=STANFORD,
        license=License.STANFORD,
        description="Decimated scan of the Lucy angel statue.",
        tags={"mesh", "polydata", "scan", "ply"},
        reference=STANFORD_URL,
    ),
)

NEFERTITI = DataSet(
    name="nefertiti",
    location=pyvista(
        "Nefertiti.obj.zip",
        "800843b48db7b061c26a453c126591f39b8cd9f903640fbb7688ab937ac5704a",
        21582417,
        uncompress=True,
    ),
    entry="Nefertiti.obj",
    metadata=MetaData(
        author=NEFERTITI_AUTHOR,
        license=License.CC_BY_NC_SA_4,
        description="High resolution 3D scan of the bust of Nefertiti.",
        tags={"mesh", "polydata", "scan", "obj"},
        reference="https://nefertitihack.alloversky.com/",
    ),
)

CARBURETOR = DataSet(
    name="carburetor",
    location=pyvista(
        "carburetor.ply",
        "f0b4b240f91c271c763b5ac95c47bcfa7e1f9410e77fa359ca07092144e946e6",
        9516099,
    ),
    metadata=MetaData(
        author=PYVISTA,
        license=License.UNKNOWN,
        description="Scan of a carburetor.",
        tags={"mesh", "polydata", "scan", "cad", "ply"},
    ),
)

TURBINE_BLADE = DataSet(
    name="turbine-blade",
    location=pyvista(
        "turbineblade.ply",
        "c2850452c86e3076e0d70f77859bee942c096153f687c66b85549f3e52d809cb",
        3781928,
    ),
    metadata=MetaData(
        author=PYVISTA,
        license=License.UNKNOWN,
        description="Scan of a turbine blade.",
        tags={"mesh", "polydata", "scan", "cad", "ply"},
    ),
)

WOMAN = DataSet(
    name="woman",
    location=pyvista(
        "woman.stl",
        "179a06d0f093595b523c28aaefbaca3cb62777277c98a102c518c184918a23f9",
        15000084,
    ),
    metadata=MetaData(
        author=PYVISTA,
        license=License.UNKNOWN,
        description="Scan of a woman.",
        tags={"mesh", "polydata", "scan", "stl"},
    ),
)

COW = DataSet(
    name="cow",
    location=pyvista(
        "cow.vtp",
        "d5aa4901d186902f90e17bf3b5917541cb6cb8cf223bfeea736631df4c047652",
        60449,
    ),
    metadata=MetaData(
        author=VIEWPOINT,
        license=License.BSD,
        description="The Viewpoint cow, converted from cow.g to VTK XML.",
        tags={"mesh", "polydata", "vtp"},
    ),
)

IFLAMIGM = DataSet(
    name="iflamigm",
    location=pyvista(
        "Viewpoint/iflamigm.3ds",
        "333c87a81a9e3a0f54df1d8118c9143445de978dc2c16e632cbefc7021d19fe5",
        260468,
    ),
    metadata=MetaData(
        author=VIEWPOINT,
        license=License.BSD,
        description="Viewpoint model in the 3D Studio format, for vtk3DSImporter.",
        tags={"mesh", "scene", "3ds"},
    ),
)

TEAPOT = DataSet(
    name="teapot",
    location=pyvista(
        "teapot.wrl",
        "c05a416193471766ce44bdcd40c6dc92d6d240591ee58aebc8e2d313a1e16985",
        57930,
    ),
    metadata=MetaData(
        author="Martin Newell (Utah teapot)",
        license=License.PUBLIC_DOMAIN,
        description="The Utah teapot, as a VRML scene.",
        tags={"mesh", "scene", "vrml"},
    ),
)

SEXTANT = DataSet(
    name="sextant",
    location=pyvista(
        "sextant.wrl",
        "8d61c9dc02d027b29fe6a0a77a8f9b099005de971ae1915125eb2bbae11863ba",
        261509,
    ),
    metadata=MetaData(
        author=VTK_EXAMPLES,
        license=License.Apache,
        description="A sextant, as a VRML scene.",
        tags={"mesh", "scene", "vrml"},
    ),
)

GRASSHOPPER = DataSet(
    name="grasshopper",
    location=pyvista(
        "grasshopper/grasshop.wrl",
        "38658f0b8c52e3b61406a6c15f55a79415e1aa662847e4120c7b2273db05caeb",
        3080151,
    ),
    metadata=MetaData(
        author=VTK_EXAMPLES,
        license=License.Apache,
        description="A grasshopper, as a VRML scene.",
        tags={"mesh", "scene", "vrml"},
        reference="https://gitlab.kitware.com/vtk/vtk-examples/-/blob/master/src/Testing/Data/grasshop.wrl",
    ),
)

DAMAGED_HELMET = DataSet(
    name="damaged-helmet",
    location=pyvista(
        "gltf/DamagedHelmet/glTF-Embedded/DamagedHelmet.gltf",
        "c0fa7be52a4c63e96af2be05735caba968b04a633a9c5eaf1b4c95fb25588003",
        5033556,
    ),
    metadata=MetaData(
        author=f"{KHRONOS}: theblueturtle_ (model), ctxwing (glTF conversion)",
        license=License.CC_BY_NC_4,
        description="Battle damaged sci-fi helmet with PBR textures.",
        tags={"mesh", "scene", "pbr", "texture", "gltf"},
        reference="https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/DamagedHelmet",
    ),
)

GEARBOX = DataSet(
    name="gearbox",
    location=pyvista(
        "gltf/GearboxAssy/glTF-Binary/GearboxAssy.glb",
        "8536ac06ec3c37e229a1eefa91803196c5cf281b8f4a88377daf0e943ce91c36",
        4958788,
    ),
    metadata=MetaData(
        author=f"{KHRONOS}: converted by Okino Computer Graphics",
        license=License.UNKNOWN,
        description="Gearbox assembly with many parts.",
        tags={"mesh", "scene", "cad", "gltf"},
        reference="https://github.com/KhronosGroupArchives/glTF-Sample-Models/tree/main/2.0/GearboxAssy",
    ),
)
