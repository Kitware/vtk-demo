"""Nested translucent surfaces, made to showcase order-independent transparency.

Scenes of the vtk.js WebGPU deep transparency gallery. Each dataset is a
directory of ``.vtp`` layers plus the gallery ``manifest.json``, which holds
the label, color and opacity of every layer and the suggested camera.
"""

from .core import DataSet, License, MetaData
from .sources import DEEP_TRANSPARENCY_REPO, deep_transparency

GALLERY_AUTHOR = "the vtk-js-deep-transparency gallery (PaulHax)"
OPEN_SCIVIS = "Open SciVis Datasets, curated by Pavol Klacansky"
OPEN_SCIVIS_URL = "https://klacansky.com/open-scivis-datasets/"

SCANS_MANIFEST = (
    "a9864236a592584b6b60da76f17e4ccbad3d0a98f4148859f6f6002661ae5b81",
    11143,
)


def _scene(name, group, files, manifest, metadata):
    """Layers of ``group/`` and its manifest, in a ``name`` directory."""
    return DataSet(
        name=name,
        location=[
            deep_transparency(f"{group}/{fname}", sha256, size, name)
            for fname, sha256, size in [*files, ("manifest.json", *manifest)]
        ],
        entry=".",
        metadata=metadata,
    )


SINUS_ANATOMY = _scene(
    "sinus-anatomy",
    "anatomy",
    [
        (
            "P001-bone.vtp",
            "75e92c2b5c73bfa434c55d2d4b1fc9236dff1bd845c3015f876c05fc57a82897",
            7553331,
        ),
        (
            "P001-right-maxillary.vtp",
            "76c2988073ff10a965832892e7cc15fdb52ddc500e0c2cb2e05b9d1fe51eb11e",
            373187,
        ),
        (
            "P001-left-maxillary.vtp",
            "f14cbf2899730e190542944a6302e6162dc05a260cd26ea6aecd955c05628b1a",
            337372,
        ),
        (
            "P001-right-nasal.vtp",
            "d8c95cfd6c05f3ef5da94bfd1bd720c1eebce90055c70fc5dd04ff4252ade316",
            923933,
        ),
        (
            "P001-left-nasal.vtp",
            "52ab53ebdfd570ae93baf5bbac75f9753b22fe6f1a314deed895a9877090e251",
            908181,
        ),
        (
            "P001-nasopharynx.vtp",
            "ce93436cb3ae4e39893ed3e6c763bcf81a42408d384ada96d17871215bcf6752",
            379314,
        ),
    ],
    (
        "bea49a64640d2d8470a11fef9b812a859842ed427c5ec8c75d768089e688f6fa",
        8171,
    ),
    MetaData(
        author="NasalSeg v2, case P001: Yichi Zhang, Jing Wang et al. (2024), "
        "converted by " + GALLERY_AUTHOR,
        license=License.CC_BY_4,
        description="Maxillary sinuses, nasal cavities and nasopharynx of a CT "
        "scan, inside the facial bone (6 .vtp surfaces).",
        tags={"medical", "mesh", "polydata", "transparency", "segmentation", "vtp"},
        reference="https://doi.org/10.5281/zenodo.13893419",
    ),
)

BEARING_ASSEMBLY = _scene(
    "bearing-assembly",
    "cad",
    [
        (
            "outer-race.vtp",
            "fe78cf34dfbc244d4e42f2fd6a7cc8e5d45060cba27d28842a1b69b0f8afe9f9",
            473495,
        ),
        (
            "inner-race.vtp",
            "cebc8fb24196f9c3fb9632c5172745dd625c98d428e031e161b8a31a33b381e3",
            470963,
        ),
        (
            "rolling-balls.vtp",
            "d346545c612d58aea8981a482142e0e700f22e30212b1f5ba6fdde4eba3ef209",
            582463,
        ),
        (
            "retainer.vtp",
            "b7c21e05a4bb39088793dab2b7bae31055b9a9a80f64a1050520baa3ae0f5f1a",
            2353433,
        ),
    ],
    (
        "4dfdccf5fcda53e49761e88962ba721118519463a02e9a8a7aa96f5a223cfa35",
        3669,
    ),
    MetaData(
        author=GALLERY_AUTHOR,
        license=License.BSD,
        description="Parametric ball bearing: inner and outer races, 12 balls "
        "and their retainer cage (4 .vtp surfaces, mm).",
        tags={"cad", "mesh", "polydata", "transparency", "vtp"},
        reference=DEEP_TRANSPARENCY_REPO,
    ),
)

ASTEROID_IMPACT_SURFACES = _scene(
    "asteroid-impact-surfaces",
    "impact",
    [
        (
            "water.vtp",
            "bf31e07fc5725948e7555595a1d2d997f6d4fc9be9557105fbe2a5def624b4aa",
            11215945,
        ),
        (
            "temperature.vtp",
            "92386c14ed2a472027a503596b4ed5b1775d02f1926522f29999c6562d26ef1c",
            8288495,
        ),
        (
            "asteroid.vtp",
            "0fc242a030f10c416872577e72fed495d1d638d8f70112ee334fdddeb6d4e560",
            8055392,
        ),
    ],
    (
        "3706884537f3324f50d86293dc51f2c58f4776af2da449e6753ac2bd730dba33",
        4685,
    ),
    MetaData(
        author="John M. Patchett and Galen R. Gisler, Los Alamos National "
        "Laboratory (LA-UR-17-21595), converted by " + GALLERY_AUTHOR,
        license=License.UNKNOWN,
        description="Deep water asteroid impact, run yA31 at 11 s: water, "
        "temperature and asteroid isosurfaces (3 .vtp surfaces).",
        tags={"simulation", "mesh", "polydata", "transparency", "isosurface", "vtp"},
        reference=DEEP_TRANSPARENCY_REPO,
    ),
)


def _scan(name, files, credit, description):
    return _scene(
        name,
        "scans",
        files,
        SCANS_MANIFEST,
        MetaData(
            author=f"{credit}, via {OPEN_SCIVIS}, converted by {GALLERY_AUTHOR}",
            license=License.UNKNOWN,
            description=description,
            tags={"ct", "mesh", "polydata", "transparency", "isosurface", "vtp"},
            reference=OPEN_SCIVIS_URL,
        ),
    )


BONSAI_SURFACES = _scan(
    "bonsai-surfaces",
    [
        (
            "bonsai-35.vtp",
            "cfc26263d7e0320dc0bc7be53429c065d42229f9758278c9ece1af51dfcac009",
            14187393,
        ),
        (
            "bonsai-100.vtp",
            "1d9208ddbffc4e2c2998ac011b56759c77a1dbfd14ba9df4c3c81d60b7a7f2e1",
            6585540,
        ),
    ],
    "volvis.org and S. Roettger, VIS, University of Stuttgart",
    "Bonsai CT scan contoured at 35 (foliage) and 100 (trunk and branches), "
    "as bonsai-*.vtp with the gallery manifest.json.",
)

ENGINE_SURFACES = _scan(
    "engine-surfaces",
    [
        (
            "engine-60.vtp",
            "673547e041e001761e230cb21bf457783c5061b5e390a8e0176edac569e1333d",
            10812203,
        ),
        (
            "engine-160.vtp",
            "0e6c4fed8a326b7f5774f82b76a8ed8d755100aa5ec6d5161995ed690fea6f39",
            2645522,
        ),
    ],
    "volvis.org and General Electric",
    "Engine block CT scan contoured at 60 (casing) and 160 (inner structure), "
    "as engine-*.vtp with the gallery manifest.json.",
)

TEAPOT_SURFACES = _scan(
    "teapot-surfaces",
    [
        (
            "teapot-50.vtp",
            "fa4f83036cce3ddcb535aaa0fe4ad6431da5cc0c4da3cf1ea113b73a22033b27",
            9711508,
        ),
        (
            "teapot-65.vtp",
            "b92ae7388c8e37c95bc00939b0e77185a196a07198bdbe485aa635a71764907a",
            1042071,
        ),
    ],
    "volvis.org and Terarecon Inc, MERL, Brigham and Women's Hospital",
    "Boston Teapot CT scan contoured at 50 (shell) and 65 (lobster inside), "
    "as teapot-*.vtp with the gallery manifest.json.",
)
