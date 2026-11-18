"""Image volumes: medical CT / MRI scans and micro-CT."""

from .core import DataSet, License, MetaData
from .sources import pyvista

VTK_DATA = "VTKData (git://vtk.org/VTKData.git)"
VTK_EXAMPLES = "VTKExamples (Bill Lorensen)"
TOTAL_SEGMENTATOR = (
    "TotalSegmentator v2.0.1 (Wasserthal et al., Radiology: AI, 2023, "
    "doi:10.1148/ryai.230024)"
)
TOTAL_SEGMENTATOR_URL = "https://zenodo.org/records/10047292"

HEAD = DataSet(
    name="head",
    location=pyvista(
        "head.vti",
        "dafa60caefb7e052a385955b609d2b7acade9c015a4122a0117473ac7a80331b",
        8848876,
    ),
    metadata=MetaData(
        author="PyVista contributors",
        license=License.UNKNOWN,
        description="CT scan of a head (256x256x94, uint16).",
        tags={"medical", "volume", "image", "ct", "vti"},
    ),
)

FULL_HEAD = DataSet(
    name="full-head",
    location=[
        pyvista(
            "FullHead.mhd",
            "96925bf993fe7ac317abeee6fdd0ba37cb78f0b3d445bc1a3d69028d51874760",
            352,
        ),
        pyvista(
            "FullHead.raw.gz",
            "086c1627b9a2a457c6eaae29a04d7ccd868ebc935c96bdf55d0d1fe8a3f01d12",
            6553235,
            uncompress=True,
        ),
    ],
    metadata=MetaData(
        author=VTK_EXAMPLES,
        license=License.Apache,
        description="CT scan of a full head (256x256x94, MetaImage).",
        tags={"medical", "volume", "image", "ct", "mhd"},
    ),
)

CHEST_CT = DataSet(
    name="chest-ct",
    location=pyvista(
        "MetaIO/ChestCT-SHORT.mha",
        "0e43b3a5b6a618d8bbb856c0bef85abb1781870c4c756b63032f24fa4653f451",
        6060126,
    ),
    metadata=MetaData(
        author=VTK_DATA,
        license=License.BSD,
        description="CT scan of a chest (MetaImage).",
        tags={"medical", "volume", "image", "ct", "mha"},
    ),
)

BRAIN = DataSet(
    name="brain",
    location=pyvista(
        "brain.vtk",
        "afd61a7e4cd7ccf64d467e92bd576cf8e98fd5c2273cb5419eb6b27569db9b2e",
        7109348,
    ),
    metadata=MetaData(
        author=VTK_EXAMPLES,
        license=License.Apache,
        description="MRI of a brain (181x217x181).",
        tags={"medical", "volume", "image", "mri", "vtk"},
    ),
)

CAROTID = DataSet(
    name="carotid",
    location=pyvista(
        "carotid.vtk",
        "3f5dac7baa8ed60fa094f67b918d55add4d55f1d498fad587d1850915f60032d",
        2681486,
    ),
    metadata=MetaData(
        author=VTK_EXAMPLES,
        license=License.Apache,
        description="Blood flow in a carotid artery, with scalar and velocity fields.",
        tags={"medical", "cfd", "volume", "image", "vector", "vtk"},
    ),
)

BANES_HEART = DataSet(
    name="banes-heart",
    location=pyvista(
        "banes_heart/banes_heart.vti",
        "be5556d5d9a6c33915d14988b4ccce2cb304901c5ab8da748e870ac7105c1669",
        27473287,
    ),
    metadata=MetaData(
        author="Bane Sullivan",
        license=License.UNKNOWN,
        description="CT scan of a heart (512x512x56).",
        tags={"medical", "volume", "image", "ct", "vti"},
    ),
)

FROG = DataSet(
    name="frog",
    location=[
        pyvista(
            "froggy/frog.mhd",
            "bfa117c99504e92cc62a4c8e68da99db2f807a93ab332f1934f6a874cff0291e",
            304,
        ),
        pyvista(
            "froggy/frog.zraw",
            "73c21b67f7e8f4f915eb262cb31b313c10e9d680b0eb537f002140902a84c7b8",
            5173190,
        ),
    ],
    metadata=MetaData(
        author=VTK_EXAMPLES,
        license=License.Apache,
        description="Scan of a frog (500x470x136, MetaImage).",
        tags={"medical", "volume", "image", "mhd"},
    ),
)

FROG_TISSUE = DataSet(
    name="frog-tissue",
    location=[
        pyvista(
            "froggy/frogtissue.mhd",
            "7fc05c76c8bce7d89056cbf4d68688431802830fbfe8a3f2dd4a1455bcd7a34b",
            309,
        ),
        pyvista(
            "froggy/frogtissue.zraw",
            "13611acf662e1aff1af64fcb8b08433b743220ccb68bd69631b6ac27dc489a85",
            262087,
        ),
    ],
    metadata=MetaData(
        author=VTK_EXAMPLES,
        license=License.Apache,
        description="Tissue labels of the frog scan (500x470x136, MetaImage).",
        tags={"medical", "volume", "image", "segmentation", "mhd"},
    ),
)

PINE_ROOT = DataSet(
    name="pine-root",
    location=pyvista(
        "PineRoot/pine_root.mha",
        "b0a6a5d0aa02f2898fc6463ec17e6ed9e59d3867338f9ac98dd37e6dd6bee7ff",
        23200609,
    ),
    metadata=MetaData(
        author=VTK_EXAMPLES,
        license=License.Apache,
        description="Micro-CT scan of a pine root (256^3, uint16).",
        tags={"biology", "volume", "image", "ct", "mha"},
    ),
)


def _whole_body_ct(name, path, sha256, size, description, tags):
    return DataSet(
        name=name,
        location=pyvista(path, sha256, size, uncompress=True),
        entry=path.rsplit("/", 1)[-1].removesuffix(".zip"),
        metadata=MetaData(
            author=TOTAL_SEGMENTATOR,
            license=License.CC_BY_4,
            description=description,
            tags={"medical", "volume", "image", "ct", "segmentation", *tags},
            reference=TOTAL_SEGMENTATOR_URL,
        ),
    )


WHOLE_BODY_CT_MALE = _whole_body_ct(
    "whole-body-ct-male",
    "whole_body_ct/s1397.zip",
    "41cdc217fbe9239ad39cca90730a4efef5d19ff6f1c3346192bb3d096848b9b0",
    62273076,
    "Whole body CT of a 74 year old male, with 117 segmented structures "
    "(ct.nii.gz and segmentations/*.nii.gz).",
    {"nifti"},
)

WHOLE_BODY_CT_FEMALE = _whole_body_ct(
    "whole-body-ct-female",
    "whole_body_ct/s1380.zip",
    "081e81cabe1c6ecf8aa466f81ebb0f791701649003ade1eaff0a0d8c384f4afe",
    58677893,
    "Whole body CT of a 78 year old female, with 117 segmented structures "
    "(ct.nii.gz and segmentations/*.nii.gz).",
    {"nifti"},
)

WHOLE_BODY_CT_MALE_RESAMPLED = _whole_body_ct(
    "whole-body-ct-male-resampled",
    "whole_body_ct/s1397_resampled.zip",
    "fd8ade8dd658d6c1db372cb7276f735483d3dfaa8292d13ed87f271a4620e7e0",
    7907179,
    "Downsampled whole body CT of a 74 year old male, one .vti per structure.",
    {"vti"},
)

WHOLE_BODY_CT_FEMALE_RESAMPLED = _whole_body_ct(
    "whole-body-ct-female-resampled",
    "whole_body_ct/s1380_resampled.zip",
    "8114e0e210652c790790242f6d6a15a5afea64e60d4c356d5d85c1f2d2b65be6",
    7260684,
    "Downsampled whole body CT of a 78 year old female, one .vti per structure.",
    {"vti"},
)
