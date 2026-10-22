import pyvista as pv
import numpy as np

n_points = 200
x = np.linspace(0, 10, n_points)
mesh = pv.PolyData(np.column_stack((x, np.sin(x), np.zeros(n_points))))
mesh.lines = np.hstack([[n_points], np.arange(n_points)])

pl = pv.Plotter()
pl.add_mesh(mesh, color="cyan", line_width=4)

t = 0.0
def update_data(step):
    global t
    t += 0.05
    mesh.points[:, 1] = np.sin(x + t)
    pl.render()  # Redraw canvas frame

# 1. Pre-initialize interactor
pl.iren.initialize()
# 2. Fire update_data every 16ms (~60 FPS)
pl.add_timer_event(max_steps=100000, duration=16, callback=update_data)
# 3. Enter blocking main window loop
pl.show()