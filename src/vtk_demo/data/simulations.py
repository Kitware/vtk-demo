"""Simulation results: finite elements (FEA), fluids (CFD) and time series."""

from .core import DataSet, License, MetaData
from .sources import pyvista

VTK_DATA = "VTKData (git://vtk.org/VTKData.git)"
VTK_EXAMPLES = "VTKExamples (Bill Lorensen)"
PYVISTA = "PyVista contributors"
SIMSCALE = "SimScale public projects"
SIMSCALE_TERMS = "https://www.simscale.com/terms-and-conditions/"

DISK_OUT_REF = DataSet(
    name="disk-out-ref",
    location=pyvista(
        "disk_out_ref.ex2",
        "e6c9d99dc0ba16b6741c22efcc986d909d0a0f6febe9a4ba3b6e4553a55b1164",
        704400,
    ),
    metadata=MetaData(
        author=VTK_DATA,
        license=License.BSD,
        description="Flow and temperature in a rotating disk reactor, the ParaView classic.",
        tags={"cfd", "multiblock", "unstructured", "vector", "exodus"},
    ),
)

CTH = DataSet(
    name="cth",
    location=pyvista(
        "cth.vtr",
        "f61e18645d1fb22ea6d9e6b0f46034b608b4ca8ffe96149c0e74a708279ce9a3",
        1059393,
    ),
    metadata=MetaData(
        author=VTK_DATA,
        license=License.BSD,
        description="CTH shock physics simulation of a projectile hitting an armor plate.",
        tags={"physics", "rectilinear", "vector", "vtr"},
    ),
)

KITCHEN = DataSet(
    name="kitchen",
    location=pyvista(
        "kitchen.vtk",
        "cf50c31bd065aedbfca8074522a3aa278ab1007273e95a8cc4e5d279834b9a25",
        2950444,
    ),
    metadata=MetaData(
        author=f"{VTK_EXAMPLES}: Dr. Ludwig Besse (ETH)",
        license=License.Apache,
        description="Air flow in a Swiss kitchen, ideal for streamlines.",
        tags={"cfd", "structured", "vector", "vtk"},
    ),
)

DISC_BIQUADRATIC = DataSet(
    name="disc-biquadratic-quads",
    location=pyvista(
        "Disc_BiQuadraticQuads_0_0.vtu",
        "2a14e4416fa751033253c0f78f58d04901bf0cd2bbaca369816e69bcd352d9f9",
        60180,
    ),
    metadata=MetaData(
        author=VTK_EXAMPLES,
        license=License.Apache,
        description="Disc made of bi-quadratic quads (higher order cells).",
        tags={"fea", "unstructured", "higher-order", "vtu"},
    ),
)

NOTCH_DISPLACEMENT = DataSet(
    name="notch-displacement",
    location=pyvista(
        "notch_disp_v2.vtu",
        "ad97dad0fe4236111fa5abb59a9257cf94f1c62fc604602e39365710af2a33dd",
        697416,
    ),
    metadata=MetaData(
        author=PYVISTA,
        license=License.UNKNOWN,
        description="Nodal displacement of a notched plate (quadratic cells).",
        tags={"fea", "unstructured", "vector", "higher-order", "vtu"},
    ),
)

NOTCH_STRESS = DataSet(
    name="notch-stress",
    location=pyvista(
        "notch_stress_fixed_v2.vtk",
        "d8e3b73dee8714857d316e3de86b75b6632595209a72a211bdbe027a10ac6c27",
        478122,
    ),
    metadata=MetaData(
        author=PYVISTA,
        license=License.UNKNOWN,
        description="Stress in a notched plate (quadratic cells).",
        tags={"fea", "unstructured", "higher-order", "vtk"},
    ),
)

AERO_BRACKET = DataSet(
    name="aero-bracket",
    location=pyvista(
        "fea/aero_bracket/aero_bracket_v2.vtu",
        "fa8aed579d5b5e6b43fa4592aaeb0083673d343ef075d21b94580ca18586156b",
        14710205,
    ),
    metadata=MetaData(
        author=SIMSCALE,
        license=License.SIMSCALE,
        description="Static stress analysis of an aircraft engine bearing bracket "
        "(quadratic tetrahedra).",
        tags={"fea", "unstructured", "higher-order", "vtu"},
        reference=SIMSCALE_TERMS,
    ),
)

FEA_BRACKET = DataSet(
    name="fea-bracket",
    location=pyvista(
        "fea/kiefer/dataset.vtu",
        "bc4856de9425095972022e79de8f4145df3ba99b09053f3315d7131f7e4e1324",
        2994777,
    ),
    metadata=MetaData(
        author="Steve Kiefer",
        license=License.UNKNOWN,
        description="Von Mises stress in a bracket.",
        tags={"fea", "unstructured", "vtu"},
        reference="https://github.com/shkiefer/dash_vtk_unstructured",
    ),
)

HERTZIAN_CONTACT = DataSet(
    name="hertzian-contact-cylinder",
    location=pyvista(
        "fea/hertzian_contact_cylinder/Hertzian_cylinder_on_plate.zip",
        "57a4faa0cc73c91e1411c17e5e11ec8a74a33f3c36a80630bee21f3fc0776256",
        7362495,
        uncompress=True,
    ),
    entry="bfac9fd1-e982-4825-9a95-9e5d8c5b4d3e_result_1.pvtu",
    metadata=MetaData(
        author="OnScale Solve",
        license=License.UNKNOWN,
        description="Hertzian contact of a cylinder on a plate, in 16 partitions.",
        tags={"fea", "unstructured", "partitioned", "pvtu"},
    ),
)

COOLING_ELECTRONICS = DataSet(
    name="cooling-electronics",
    location=pyvista(
        "fvm/cooling_electronics/datasets_v2.zip",
        "2ef0d8322dd6f36ed07c89c23d429eb7f04f466770284762047b0e33a93a19e5",
        50205658,
        uncompress=True,
    ),
    metadata=MetaData(
        author=SIMSCALE,
        license=License.SIMSCALE,
        description="Conjugate heat transfer in an electronics box: air.vtu (flow) "
        "and structure.vtp (components).",
        tags={"cfd", "thermal", "unstructured", "polydata", "vector", "vtu", "vtp"},
        reference="https://www.simscale.com/docs/tutorials/thermal-management-cht-analysis-electronics-box/",
    ),
)

TURBO_INCOMPRESSIBLE = DataSet(
    name="turbo-incompressible",
    location=pyvista(
        "fvm/turbo_incompressible/Turbo-Incompressible_3-Run_1-SOLUTION_FIELDS.zip",
        "4f615c2d7644e7ee504b9c548c8ef9095bfaaf19ac2a7071516f8978cbcc5385",
        38228176,
        uncompress=True,
    ),
    entry="case.foam",
    metadata=MetaData(
        author=SIMSCALE,
        license=License.SIMSCALE,
        description="Incompressible flow through a turbomachine (OpenFOAM case).",
        tags={"cfd", "turbomachinery", "multiblock", "vector", "openfoam"},
        reference="https://www.simscale.com/projects/ayarnoz/turbo/",
    ),
)

LETHE_PARTICLES = DataSet(
    name="lethe-particles",
    location=pyvista(
        "lethe/result_particles.20000.0000.vtu",
        "b7bf4ff0fee5af4f948e8838c4f9429585e5e894094440b32c9cef780ab59b21",
        7171334,
    ),
    metadata=MetaData(
        author="Lethe",
        license=License.UNKNOWN,
        description="Discrete element simulation of ~5k particles.",
        tags={"cfd", "particles", "point-cloud", "unstructured", "vtu"},
        reference="https://github.com/lethe-cfd/lethe",
    ),
)

WAVY = DataSet(
    name="wavy",
    location=pyvista(
        "vtu_series/wavy.zip",
        "c603bece678443a1cfb044835379bb0987690426aef8d45dc0b7fbc693e248ab",
        1117005,
        uncompress=True,
    ),
    entry="mesh.vtu.series",
    metadata=MetaData(
        author=PYVISTA,
        license=License.UNKNOWN,
        description="Animated wavy surface, 15 time steps (.vtu.series).",
        tags={"time-series", "unstructured", "vtu"},
    ),
)

WARPING_SPHERES = DataSet(
    name="warping-spheres",
    location=pyvista(
        "warping_spheres/warping_spheres.vtkhdf",
        "11aeb0593838672f9615804377a9434486173c16121c5b42210727d8cac726af",
        3068512,
    ),
    metadata=MetaData(
        author="VTK examples",
        license=License.BSD,
        description="Animated warping spheres, a transient VTKHDF file.",
        tags={"time-series", "polydata", "vtkhdf"},
        reference="https://gitlab.kitware.com/vtk/vtk-examples/-/blob/master/src/Testing/Data/warping_spheres.vtkhdf",
    ),
)
