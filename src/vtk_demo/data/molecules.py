"""Molecular structures (PDB) and molecular volumes."""

from .core import DataSet, License, MetaData
from .sources import pyvista

RCSB = "RCSB Protein Data Bank"
VTK_DATA = "VTKData (git://vtk.org/VTKData.git)"
VTK_EXAMPLES = "VTKExamples (Bill Lorensen)"

PDB_2LYZ = DataSet(
    name="2lyz",
    location=pyvista(
        "2LYZ.pdb",
        "aa97b5e2f06608346654c150ab15d50977fa3505fea617b7959885ec5583cc06",
        135189,
    ),
    metadata=MetaData(
        author=RCSB,
        license=License.CC0,
        description="Hen egg-white lysozyme (PDB 2LYZ), used for protein ribbon rendering.",
        tags={"chemistry", "molecule", "protein", "pdb"},
        reference="https://www.rcsb.org/structure/2LYZ",
    ),
)

PDB_2J6G = DataSet(
    name="2j6g",
    location=pyvista(
        "2j6g.pdb",
        "7c48c4ca406d27d3ff03193d9504ffa87b136fd4715fc7145df768ae4e8d8f31",
        204120,
    ),
    metadata=MetaData(
        author=RCSB,
        license=License.CC0,
        description="Protein structure PDB 2J6G.",
        tags={"chemistry", "molecule", "protein", "pdb"},
        reference="https://www.rcsb.org/structure/2J6G",
    ),
)

PDB_3GQP = DataSet(
    name="3gqp",
    location=pyvista(
        "3GQP.pdb",
        "4bf8c6f493546ceaa16dc0798709985b3ba3bfee41d7198a8f541e24a38398d7",
        446634,
    ),
    metadata=MetaData(
        author=RCSB,
        license=License.CC0,
        description="Protein structure PDB 3GQP, used to test vtkProteinRibbonFilter.",
        tags={"chemistry", "molecule", "protein", "pdb"},
        reference="https://www.rcsb.org/structure/3GQP",
    ),
)

CAFFEINE = DataSet(
    name="caffeine",
    location=pyvista(
        "caffeine.pdb",
        "b1e6124e492ac52521ffa59a699e7197e4a71fcef52a7e5c12c151f4db8c76be",
        2025,
    ),
    metadata=MetaData(
        author=VTK_DATA,
        license=License.BSD,
        description="Caffeine molecule, a small PDB file for molecule readers.",
        tags={"chemistry", "molecule", "pdb"},
    ),
)

LYSOZYME = DataSet(
    name="lysozyme",
    location=pyvista(
        "lys.pdb",
        "ee2f7dfb8d6fb37d07ac5d2488dfa74b56dbb0862309600567d66eac5cfc27e1",
        1810,
    ),
    metadata=MetaData(
        author=VTK_EXAMPLES,
        license=License.Apache,
        description="Small lysozyme PDB file from the VTK examples.",
        tags={"chemistry", "molecule", "protein", "pdb"},
    ),
)

IRON_PROTEIN = DataSet(
    name="iron-protein",
    location=pyvista(
        "ironProt.vtk",
        "544f67d66dbb8b79e48053f131d614e225d0caa702fd3f690313312dd4119f79",
        314642,
    ),
    metadata=MetaData(
        author=VTK_DATA,
        license=License.BSD,
        description="Iron protein density, a classic 68x68x68 volume rendering example.",
        tags={"chemistry", "volume", "image", "vtk"},
    ),
)

HYDROGEN = DataSet(
    name="hydrogen-orbital",
    location=pyvista(
        "hydrogen/hydrogen.vti",
        "9cb09f8610163b03d80a4e95d5b67e89822f38d7559c64efb12b9235b02b8877",
        298712,
    ),
    metadata=MetaData(
        author="Uppsala University visualization course",
        license=License.UNKNOWN,
        description="Probability density of the 3d orbital of the hydrogen atom (64^3 volume).",
        tags={"physics", "chemistry", "volume", "image", "vti"},
        reference="https://github.com/pyvista/data/tree/master/Data/hydrogen",
    ),
)
