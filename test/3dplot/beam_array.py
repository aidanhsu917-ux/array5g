import numpy as np
import pandas as pd
import pyvista as pv

# 1. Load matrix (assumes header contains theta values, index contains phi values)
df = pd.read_csv("DATA.csv", skiprows=1)

# 2. Extract angles from headers/index (convert to radians if they are in degrees)
theta_degrees = df.columns[2:].astype(float).values
u_theta = np.radians(theta_degrees)

phi_degrees = df.iloc[1:, 1].astype(float).values
u_phi = np.radians(phi_degrees)

# 3. Extract the gain values as a 2D array
r = df.iloc[1:, 2:].astype(float).to_numpy()  # Shape should be (len(u_phi), len(u_theta))

if r.min() < 0:
    r = 10**(r / 10)  # Convert dB to linear scale if necessary




# Handle negative or zero dB values if necessary (e.g., floor them so the pattern doesn't turn inside out)
# r = np.clip(r, 0, None) # If linear
# r = r - r.min()        # If dB, shifting to keep all radius values positive

# # 4. Create coordinate meshgrids
THETA, PHI = np.meshgrid(u_theta, u_phi)

# 5. Convert to Cartesian coordinates
X = r * np.sin(THETA) * np.cos(PHI)
Y = r * np.sin(THETA) * np.sin(PHI)
Z = r * np.cos(THETA)


# 6. Build and render PyVista grid
grid = pv.StructuredGrid(X, Y, Z)
grid["Gain"] = r.flatten(order="C")

# --- THE FIX: Extract surface, triangulate, and WELD the seam points ---
surface = grid.extract_surface().triangulate()

# tolerance=1e-5 finds the overlapping -180 and 180 points and welds them closed
closed_surface = surface.clean(tolerance=1e-5)

# Now subdivide the perfectly sealed mesh
smooth_surface = closed_surface.subdivide(2, subfilter="butterfly")

plotter = pv.Plotter()
plotter.add_mesh(smooth_surface, scalars="Gain", cmap="turbo", show_edges=False, smooth_shading=True)
plotter.add_axes()
plotter.show()

