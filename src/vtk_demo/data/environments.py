"""Textures, sky boxes, cube maps and astronomy."""

from .core import DataSet, License, MetaData
from .sources import pyvista

NASA_SVS = (
    "NASA/Goddard Space Flight Center Scientific Visualization Studio, "
    "Gaia DR2: ESA/Gaia/DPAC"
)

SKYBOX = DataSet(
    name="skybox",
    location=[
        pyvista(f"skybox/skybox-{face}.jpg", sha256, size)
        for face, sha256, size in [
            (
                "posx",
                "bf20acd6817c9e7073e485bbe2d2ce56dacff73c021c2b613ba072ba2df2b754",
                60050,
            ),
            (
                "negx",
                "12b1ce6c91aa3aaf258a8a5944df739a6c1cc76e89d4d7119d1f795a30fc1bf2",
                55756,
            ),
            (
                "posy",
                "16f0d692af0b80e46929d8d8a7e596123c76729cc5eb7dfd1c9184b115dd143a",
                19634,
            ),
            (
                "negy",
                "e18fe2206b63d3df2c879f5e0b9937a61d99734b6c43ac288226c58d2418d23e",
                52198,
            ),
            (
                "posz",
                "b850b5e882889df26be9289d7c25ba30524b37e56bc2075b968a83197ad977f3",
                58868,
            ),
            (
                "negz",
                "00dddd1b715d5877af2a74c014ff6e47891f07435b471d213cd0673a8c47f2b2",
                54574,
            ),
        ]
    ],
    entry=".",
    metadata=MetaData(
        author="VTKExamples (Bill Lorensen)",
        license=License.Apache,
        description="Sky box, as six skybox-{pos,neg}{x,y,z}.jpg cube map faces.",
        tags={"environment", "texture", "cubemap", "jpg"},
        reference="https://github.com/lorensen/VTKExamples",
    ),
)

CUBEMAP_SPACE_4K = DataSet(
    name="cubemap-space-4k",
    location=pyvista(
        "cubemap_space/4k.zip",
        "5df40ba4bb18baa0b460a1d24925a3de030649d31ff986ddb9f1cf505a2abd6f",
        1534453,
        uncompress=True,
    ),
    metadata=MetaData(
        author=NASA_SVS,
        license=License.UNKNOWN,
        description="Milky Way star map, as six {pos,neg}{x,y,z}.jpg cube map faces (4k).",
        tags={"environment", "astronomy", "texture", "cubemap", "jpg"},
        reference="https://svs.gsfc.nasa.gov/4851",
    ),
)

CUBEMAP_SPACE_16K = DataSet(
    name="cubemap-space-16k",
    location=pyvista(
        "cubemap_space/16k.zip",
        "4c21a2b339d23b5921a90351ba20366f7a84d75fd3e81a56af7dcb77aa12c7c1",
        39453294,
        uncompress=True,
    ),
    metadata=MetaData(
        author=NASA_SVS,
        license=License.UNKNOWN,
        description="Milky Way star map, as six {pos,neg}{x,y,z}.jpg cube map faces (16k).",
        tags={"environment", "astronomy", "texture", "cubemap", "jpg"},
        reference="https://svs.gsfc.nasa.gov/4851",
    ),
)

_SOLAR_TEXTURES = [
    (
        "sun.jpg",
        "ff0f076ba65e03b5ab518451bc96699325be38e3ccbdd5869ee1c00f3a0c8816",
        822427,
    ),
    (
        "mercury.jpg",
        "5a5c80607f643496bac9a631e71957def35ed788895f18b678ac849c2b38e48a",
        872555,
    ),
    (
        "venus_surface.jpg",
        "dbe5db1c794a8ab4cbf7dd6bf193540c400fc833ce1e6cc399318aa68026278b",
        885075,
    ),
    (
        "venus_atmosphere.jpg",
        "225012ad4911730605c4e189ca2a3bf674fce50cc48aab4102b936b47d6991ac",
        229696,
    ),
    (
        "moon.jpg",
        "2764ba6535ea0481a062846ee033cc7a909dae05b31a8fd13f3e98f3a7fd92bd",
        1053869,
    ),
    (
        "mars.jpg",
        "88d631422f4184dfd8f5afb6429637bea5a59bb1e78fd676512c86b56480be18",
        620353,
    ),
    (
        "jupiter.jpg",
        "b0f04d005350252636b0e3396fc592548cbd9e9126b269d32d5c6abd4b0e4f2b",
        498976,
    ),
    (
        "saturn.jpg",
        "54a900ca9bf7ab62e70f862852759abdf342e6d6436a95a2fe9ebdb6bcd3bbac",
        199916,
    ),
    (
        "saturn_ring_alpha.png",
        "4b0644b2f3ef259fd0bfaedd9dc52f9e7d9738f65f50363e8c4dd19f650d7334",
        12119,
    ),
    (
        "uranus.jpg",
        "d15239d46f82d3ea13d2b260b5b29b2a382f42f2916dae0694d0387b1204a09d",
        77751,
    ),
    (
        "neptune.jpg",
        "cb42ea82709741d28b0af44d8b283cbc6dbd0c521a7f0e1e1e010ade00977df6",
        241580,
    ),
    (
        "pluto.jpg",
        "e36f3daa1b3b0e911418ff830ddccf8b63e10a082c6ccc96eb7d8170991962d6",
        1423389,
    ),
]

SOLAR_TEXTURES = DataSet(
    name="solar-textures",
    location=[
        pyvista(f"solar_textures/{name}", sha256, size)
        for name, sha256, size in _SOLAR_TEXTURES
    ],
    entry=".",
    metadata=MetaData(
        author="Solar System Scope",
        license=License.CC_BY_4,
        description="Textures of the sun, planets, moon and Saturn's rings.",
        tags={"astronomy", "texture", "jpg", "png"},
        reference="https://www.solarsystemscope.com/textures/",
    ),
)

STARS = DataSet(
    name="stars",
    location=pyvista(
        "point-clouds/hyg-database/stars.vtp",
        "09584c832abcfb04a01e027a9454c528beeee50ecb0c5b580d23454039925888",
        3193960,
    ),
    metadata=MetaData(
        author="HYG-Database (astronexus)",
        license=License.CC_BY_SA_2_5,
        description="~108k stars of the HYG catalog with their luminosity.",
        tags={"astronomy", "point-cloud", "polydata", "vtp"},
        reference="https://github.com/astronexus/HYG-Database",
    ),
)
