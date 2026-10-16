"""Show the plain VTK scenes of :mod:`vtk_demo.scenes` in a PyVista plotter.

    import pyvista as pv
    from vtk_demo.pyvista_adapter import add_scene
    from vtk_demo.scenes import build_glyph_island

    plotter = pv.Plotter()
    n_actors, n_instances, n_triangles = add_scene(plotter, build_glyph_island)
    plotter.show()

The scenes themselves are plain VTK: PyVista only comes in here, in the
applications.
"""


def add_scene(plotter, build, *args, **kwargs):
    """Return ``build(plotter.renderer, *args, **kwargs)``, keeping the scene's camera.

    The scenes add their actors straight to the ``vtkRenderer`` that PyVista
    wraps, which skips PyVista's per actor bookkeeping: that matters with tens
    of thousands of actors. They also place the camera, which PyVista (and
    trame-pyvista) would reset on the first render unless told it is set.
    """
    result = build(plotter.renderer, *args, **kwargs)
    plotter.renderer.camera.is_set = True
    return result
