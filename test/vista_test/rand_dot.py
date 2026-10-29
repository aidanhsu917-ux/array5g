import numpy as np
import pyvista as pv

rng = np.random.default_rng()

def main():
    plotter = pv.Plotter()

    r_max = 3.0  # Maximum radius of the coordinate grid

    # -------------------------------------------------------------------------
    # 2. Azimuth (Phi) Angle Labels - Equatorial Plane (XY)
    # -------------------------------------------------------------------------
    phi_angles = np.linspace(0, 360, 16, endpoint=False)  # [0°, 45°, 90°, ..., 315°]
    phi_rad = np.radians(phi_angles)

    # Position labels slightly beyond the outer wireframe boundary
    r_phi_label = r_max * 1.15
    phi_points = np.column_stack([
        r_phi_label * np.cos(phi_rad),
        r_phi_label * np.sin(phi_rad),
        np.zeros_like(phi_rad)
    ])
    phi_labels = [f"phi = {int(a)}°" for a in phi_angles]

    # Draw radial reference lines for phi
    for rad in phi_rad:
        line_end = (r_max * np.cos(rad), r_max * np.sin(rad), 0)
        line_end_theta = (r_max *np.cos(rad), 0, r_max * np.sin(rad))
        plotter.add_mesh(pv.Line((0, 0, 0), line_end), color='royalblue', opacity=0.5, line_width=1)
        plotter.add_mesh(pv.Line((0, 0, 0), line_end_theta), color='crimson', opacity=0.5, line_width=1)

    # Add azimuth labels
    plotter.add_point_labels(
        phi_points,
        phi_labels,
        font_size=12,
        text_color="royalblue",
        shape_opacity=0,       # Transparent label background
        always_visible=True    # Render over geometry without occlusion
    )

    # -------------------------------------------------------------------------
    # 3. Elevation (Theta) Angle Labels - Vertical Arc (XZ Plane)
    # -------------------------------------------------------------------------
    # theta_angles = np.array([-90, -45, 0, 45, 90])  # South pole to North pole
    # theta_rad = np.radians(theta_angles)
    r_theta_label = r_max * 1.15
    # Position labels along the XZ meridian plane
    theta_points = np.column_stack([
        r_theta_label * np.cos(phi_rad),
        np.zeros_like(phi_rad),
        r_theta_label * np.sin(phi_rad)
    ])
    theta_labels = [f"theta = {int(a)}°" for a in phi_angles]

    # Draw vertical meridian ring for theta
    meridian = pv.Circle(radius=r_max, resolution=64)
    meridian.rotate_x(90, inplace=True)
    plotter.add_mesh(meridian, style='wireframe', color='crimson', opacity=0.5, line_width=1.5)
    meridian_2 = pv.Circle(radius = r_max, resolution= 64)
    plotter.add_mesh(meridian_2, style='wireframe', color='royalblue', opacity=0.5, line_width=1.5)

    # Add elevation labels
    plotter.add_point_labels(
        theta_points,
        theta_labels,
        font_size=12,
        text_color="crimson",
        shape_opacity=0,
        always_visible=True
    )

    mesh = pv.Sphere(radius=0.1) 
    actor = plotter.add_mesh(mesh)

    plotter.iren.initialize()

    def update_data(step):
            #step is the number of times the event has happened
            # mesh.points[:, 1] = np.sin(x + t)
            # pl.render()  # Redraw canvas frame
            phi = .25 * 2 * np.pi
            theta = rng.random() * 2 * np.pi

            x = 3 * np.sin(phi) * np.cos(theta)
            y = 3 * np.sin(phi) * np.sin(theta)
            z = 3 * np.cos(phi)

            print(x, y, z)

            actor.position = [x, y, z]

    plotter.add_timer_event(max_steps = 10000000, duration= 1000, callback=update_data)
    #for continuous, do not include max_steps
    #duration in ms

    plotter.show()
    
    

if __name__ == "__main__":
    main()