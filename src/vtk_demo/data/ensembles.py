"""Ensembles of scalar fields, curated for topological data analysis (TTK).

Members of the ensembles of "Wasserstein Distances, Geodesics and Barycenters
of Merge Trees" (Pont, Vidal, Delon, Tierny, IEEE VIS 2021), mostly from the
IEEE SciVis contests. Each ``wmt-*`` dataset is a directory with one file per
member, holding its ground truth (``ClusterID``, ``TimeStep``...) as field
data.

The ``wmt-*`` datasets share a single 8.5 GB archive, downloaded once and
kept in the cache: each dataset only extracts its own ensemble out of it.
The ``vidal-*`` datasets share a 784 MB zip, where each ensemble is a single
file with one point array per member.
"""

from .core import ArchiveMember, DataSet, License, MetaData, RemoteLocation
from .sources import google_drive_url

WMT_AUTHOR = (
    "Mathieu Pont, Jules Vidal, Julie Delon, Julien Tierny (Wasserstein Merge "
    "Trees, IEEE VIS 2021, doi:10.1109/TVCG.2021.3114839)"
)
WMT_REFERENCE = (
    "https://github.com/MatPont/WassersteinMergeTreesData/tree/"
    "76a681ace218a813c17efa13db4b1cd061e8959b"
)
WMT_ARCHIVE = "wassersteinMergeTreesData.tar.xz"
WMT_SHA256 = "f1b716833582b08255ec8dfd9475f2a5e57d4d57bddabcd36098795fcb4d13fe"
WMT_SIZE = 8458609796

VIDAL_AUTHOR = (
    "Jules Vidal, Joseph Budin, Julien Tierny (Progressive Wasserstein "
    "Barycenters of Persistence Diagrams, IEEE VIS 2019, "
    "doi:10.1109/TVCG.2019.2934256)"
)
VIDAL_LOCATION = RemoteLocation(
    url=google_drive_url("1fxPAUmYT4UAUHh7K0w83znckyw_NTLan"),
    known_hash="sha256:13457c3639830f3464ba7e753c18939e6b915e08f77b6135fd49cda0de0e112f",
    uncompress=True,
    fname="wasserstein-merge-trees/vidal-ensembles.zip",
    size=783950568,
)


def _wmt(name, ensemble, description, tags):
    return DataSet(
        name=name,
        location=ArchiveMember(
            url=google_drive_url("14dx5Fjw0PnBgYwzVkU7iD8jf5lW8ZNDf"),
            known_hash=f"sha256:{WMT_SHA256}",
            fname=f"wasserstein-merge-trees/{WMT_ARCHIVE}",
            size=WMT_SIZE,
            member=f"wassersteinMergeTreesData/{ensemble}.tar.xz",
        ),
        metadata=MetaData(
            author=WMT_AUTHOR,
            license=License.UNKNOWN,
            description=description,
            tags={"ensemble", "ttk", "unstructured", "vtu", *tags},
            reference=WMT_REFERENCE,
        ),
    )


def _vidal(name, entry, description, tags):
    return DataSet(
        name=name,
        location=VIDAL_LOCATION,
        entry=f"data/{entry}",
        metadata=MetaData(
            author=VIDAL_AUTHOR,
            license=License.UNKNOWN,
            description=description,
            tags={"ensemble", "ttk", *tags},
            reference=WMT_REFERENCE,
        ),
    )


# -----------------------------------------------------------------------------
# Wasserstein Merge Trees curated ensembles (one directory of .vtu each)
# -----------------------------------------------------------------------------

WMT_ASTEROID_IMPACT_TS = _wmt(
    "wmt-asteroid-impact-temporal",
    "2018_asteroid_impact_3D_temporal_subsampling",
    "SciVis 2018 deep water asteroid impact, run yA31: 20 time steps in "
    "4 clusters (300^3, smoothed). Extracts to ~10 GB.",
    {"simulation", "time-series"},
)

WMT_ASTEROID_IMPACT = _wmt(
    "wmt-asteroid-impact-clustering",
    "2018_asteroid_impact_3D_clustering",
    "SciVis 2018 deep water asteroid impact: last time step of 7 runs, "
    "clustered by asteroid diameter (300^3). Extracts to 3.6 GB.",
    {"simulation"},
)

WMT_CLOUD_PROCESSES = _wmt(
    "wmt-cloud-processes",
    "2017_cloud_processes_2D",
    "SciVis 2017 cloud processes: 12 time steps of the cloud cover ('ccb', "
    "1430x1557, smoothed) in 3 clusters. Extracts to 2.2 GB.",
    {"simulation", "atmosphere", "2d"},
)

WMT_VISCOUS_FINGERING = _wmt(
    "wmt-viscous-fingering",
    "2016_viscous_fingering_3D",
    "SciVis 2016 viscous fingering: salt concentration of 15 runs resampled "
    "on 50^3, clustered by smoothing length. Extracts to 400 MB.",
    {"simulation", "cfd"},
)

WMT_DARK_MATTER = _wmt(
    "wmt-dark-matter",
    "2015_dark_matter_3D",
    "SciVis 2015 Dark Sky: dark matter density of 40 time steps splatted "
    "on 100^3, in 4 clusters. Extracts to 8.8 GB.",
    {"simulation", "astrophysics", "time-series"},
)

WMT_VOLCANIC_ERUPTIONS = _wmt(
    "wmt-volcanic-eruptions",
    "2014_volcanic_eruptions_2D",
    "SciVis 2014 volcanic eruptions: 12 AIRS measures of SO2 (500x500, "
    "simplified) in 3 clusters. Extracts to 300 MB.",
    {"atmosphere", "geoscience", "2d"},
)

WMT_IONIZATION_FRONT_2D = _wmt(
    "wmt-ionization-front-2d",
    "2008_ionization_front_2D",
    "SciVis 2008 ionization front: density of 16 time steps on a 2D slice "
    "(600x248, normalized) in 4 clusters. Extracts to 200 MB.",
    {"simulation", "astrophysics", "time-series", "2d"},
)

WMT_IONIZATION_FRONT_3D = _wmt(
    "wmt-ionization-front-3d",
    "2008_ionization_front_3D",
    "SciVis 2008 ionization front: density of 16 time steps (300x124x124, "
    "normalized) in 4 clusters. Extracts to 16.5 GB.",
    {"simulation", "astrophysics", "time-series"},
)

WMT_EARTHQUAKE = _wmt(
    "wmt-earthquake",
    "2006_earthquake_3D",
    "SciVis 2006 TeraShake earthquake: velocity magnitude of 12 time steps "
    "(375x188x50, simplified) in 3 clusters. Extracts to 2.2 GB.",
    {"simulation", "geoscience", "time-series"},
)

# -----------------------------------------------------------------------------
# Vidal et al. 2019 ensembles (one file each, one point array per member)
# -----------------------------------------------------------------------------

VIDAL_ISABEL = _vidal(
    "vidal-isabel",
    "isabella_velocity_goodEnsemble.vti",
    "Hurricane Isabel: wind velocity magnitude of 12 members (250x250x50), "
    "one point array per member.",
    {"simulation", "atmosphere", "volume", "image", "vti"},
)

VIDAL_SEA_SURFACE_HEIGHT = _vidal(
    "vidal-sea-surface-height",
    "seaSurfaceHeightGoodEnsemble.vti",
    "Sea surface height of 48 days of 2012 (1440x720), one point array per member.",
    {"geoscience", "ocean", "image", "2d", "vti"},
)

VIDAL_STARTING_VORTEX = _vidal(
    "vidal-starting-vortex",
    "startingVortexGoodEnsemble.vti",
    "Starting vortex: vorticity for 12 angles (1500x1000), one point array per member.",
    {"simulation", "cfd", "image", "2d", "vti"},
)

VIDAL_VORTEX_STREET = _vidal(
    "vidal-vortex-street",
    "vortexStreetGoodEnsemble2.vti",
    "Von Karman vortex street behind a cylinder: 45 members (300x100), one "
    "point array per member.",
    {"simulation", "cfd", "image", "2d", "vti"},
)

VIDAL_GAUSSIANS = _vidal(
    "vidal-gaussians",
    "main_example.vtu",
    "Synthetic ensemble of 100 mixtures of Gaussians (513x513 triangulated), "
    "one point array per member.",
    {"synthetic", "unstructured", "2d", "vtu"},
)

VIDAL_PERSISTENCE_DIAGRAMS = _vidal(
    "vidal-persistence-diagrams",
    "diagrams",
    "TTK persistence diagrams of every member of the Vidal et al. ensembles "
    "(gaussians, isabel, seaSurfaceHeight, startingVortex, vortexStreet).",
    {"persistence-diagram", "unstructured", "vtu"},
)
