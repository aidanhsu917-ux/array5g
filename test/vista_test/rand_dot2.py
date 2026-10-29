import numpy as np
import pyvista as pv

rng = np.random.default_rng()

def align_mesh_to_vector(target_vector, base_axis=(0, 0, 1)):
    """
    Generates a 4x4 transformation matrix to point a base axis (default Z-axis)
    toward a target vector coordinate.
    """
    target = np.array(target_vector, dtype=float)
    norm = np.linalg.norm(target)
    if norm == 0:
        return np.eye(4)
    
    # Normalized direction vector
    z_prime = target / norm
    
    # Pick a temporary vector to compute orthoganal axes (handle edge case if parallel)
    tmp = np.array([1.0, 0.0, 0.0]) if abs(z_prime[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    
    x_prime = np.cross(tmp, z_prime)
    x_prime /= np.linalg.norm(x_prime)
    y_prime = np.cross(z_prime, x_prime)
    
    # Construct rotation matrix
    mat = np.eye(4)
    mat[:3, 0] = x_prime
    mat[:3, 1] = y_prime
    mat[:3, 2] = z_prime
    return mat

def main():
    plotter = pv.Plotter()

    r_max = 3.0  # Maximum radius of the coordinate grid

    # -------------------------------------------------------------------------
    # 2. Azimuth (Phi) Angle Labels - Equatorial Plane (XY)
    # -------------------------------------------------------------------------
    phi_angles = np.linspace(0, 360, 16, endpoint=False)
    phi_rad = np.radians(phi_angles)

    r_phi_label = r_max * 1.15
    phi_points = np.column_stack([
        r_phi_label * np.cos(phi_rad),
        r_phi_label * np.sin(phi_rad),
        np.zeros_like(phi_rad)
    ])
    phi_labels = [f"phi = {int(a)}°" for a in phi_angles]

    for rad in phi_rad:
        line_end = (r_max * np.cos(rad), r_max * np.sin(rad), 0)
        line_end_theta = (r_max *np.cos(rad), 0, r_max * np.sin(rad))
        plotter.add_mesh(pv.Line((0, 0, 0), line_end), color='royalblue', opacity=0.5, line_width=1)
        plotter.add_mesh(pv.Line((0, 0, 0), line_end_theta), color='crimson', opacity=0.5, line_width=1)

    plotter.add_point_labels(
        phi_points,
        phi_labels,
        font_size=12,
        text_color="royalblue",
        shape_opacity=0,
        always_visible=True
    )

    # -------------------------------------------------------------------------
    # 3. Elevation (Theta) Angle Labels - Vertical Arc (XZ Plane)
    # -------------------------------------------------------------------------
    r_theta_label = r_max * 1.15
    theta_points = np.column_stack([
        r_theta_label * np.cos(phi_rad),
        np.zeros_like(phi_rad),
        r_theta_label * np.sin(phi_rad)
    ])
    theta_labels = [f"theta = {int(a)}°" for a in phi_angles]

    meridian = pv.Circle(radius=r_max, resolution=64)
    meridian.rotate_x(90, inplace=True)
    plotter.add_mesh(meridian, style='wireframe', color='crimson', opacity=0.5, line_width=1.5)
    meridian_2 = pv.Circle(radius=r_max, resolution=64)
    plotter.add_mesh(meridian_2, style='wireframe', color='royalblue', opacity=0.5, line_width=1.5)

    plotter.add_point_labels(
        theta_points,
        theta_labels,
        font_size=12,
        text_color="crimson",
        shape_opacity=0,
        always_visible=True
    )

    mesh = pv.Sphere(radius=0.1) 
    actor = plotter.add_mesh(mesh, color="gold")
    
    # Load and scale your radiation pattern mesh
    antenna_mesh = pv.read("plot_mesh.ply")
    antenna_mesh = antenna_mesh.scale(3.5, inplace=False)
    antenna_mesh = antenna_mesh.rotate_z(90, inplace=False)
    
    # Note: If your PLY pattern mesh naturally points forward along a different axis 
    # (like X or Y), adjust the base_axis inside align_mesh_to_vector accordingly.
    antenna_actor = plotter.add_mesh(antenna_mesh, color="lime", opacity=0.7)

    plotter.iren.initialize()

    def update_data(step):
        # Generate new random target coordinates on the hemisphere
        phi = 0.25 * 2 * np.pi
        theta = rng.random() * 2 * np.pi

        x = 3 * np.sin(phi) * np.cos(theta)
        y = 3 * np.sin(phi) * np.sin(theta)
        z = 3 * np.cos(phi)

        # Update the gold sphere's location
        actor.position = [x, y, z]
        
        # Dynamically calculate the look-at transformation matrix
        # and apply it to the radiation pattern actor
        rotation_matrix = align_mesh_to_vector([x, y, z], base_axis=(0, 0, 1))
        antenna_actor.user_matrix = rotation_matrix
        
        # Force the screen to redraw the new orientation frame
        plotter.render()

    plotter.add_timer_event(max_steps = 10000000, duration= 1000, callback=update_data)
    plotter.show()

if __name__ == "__main__":
    main()
