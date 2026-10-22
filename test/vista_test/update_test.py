import pyvista as pv

sphere = pv.Sphere()

pl = pv.Plotter()
actor = pl.add_mesh(sphere)
actor2 = pl.add_mesh(pv.Line((0, 0, 0), (100, 0, 0)))


def callback(step):
    actor.position = [step / 100.0, step / 100.0, 0]

pl.iren.initialize()
pl.add_timer_event(max_steps=200, duration=500, callback=callback)

cpos = pv.CameraPosition(
    position=(0.0, 0.0, 10.0), focal_point=(0.0, 0.0, 0.0), viewup=(0.0, 1.0, 0.0)
)
pl.show(cpos=cpos)