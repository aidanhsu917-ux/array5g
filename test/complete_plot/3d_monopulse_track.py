# receiver.py
import redis
import numpy as np
import pyvista as pv

# Connect to the local Redis server
r = redis.Redis(host='localhost', port=6379, db=0)
pubsub = r.pubsub()

# Subscribe to the exact channel name used in your Pluto script
pubsub.subscribe('pluto_doa')

print("📡 Receiver online. Waiting for live Pluto DOA angles...")

# Set up a starting fallback angle so the sphere has coordinates before data streams in
live_angle = 0.0
radii = np.loadtxt("radii.csv", delimiter=",")

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
    global live_angle
    
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
        line_end_theta = (r_max * np.cos(rad), 0, r_max * np.sin(rad))
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
    r_theta_label = r_max * 1.15
    # Position labels along the XZ meridian plane
    theta_points = np.column_stack([
        r_theta_label * np.cos(phi_rad),
        np.zeros_like(phi_rad),
        r_theta_label * np.sin(phi_rad)
    ])
    theta_labels = [f"theta = {int(a)}°" for a in phi_angles]

    # Draw vertical meridian rings
    meridian = pv.Circle(radius=r_max, resolution=64)
    meridian.rotate_x(90, inplace=True)
    plotter.add_mesh(meridian, style='wireframe', color='crimson', opacity=0.5, line_width=1.5)
    meridian_2 = pv.Circle(radius=r_max, resolution=64)
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

    # Add target tracking indicator sphere
    antenna_mesh = pv.read("plot_mesh.ply")
    antenna_mesh = antenna_mesh.scale(3.5, inplace=False)
    antenna_mesh = antenna_mesh.rotate_z(90, inplace=False)
    antenna_mesh["Field Strength"] = radii.ravel(order='F')
    
    # Note: If your PLY pattern mesh naturally points forward along a different axis 
    # (like X or Y), adjust the base_axis inside align_mesh_to_vector accordingly.
    antenna_actor = plotter.add_mesh(antenna_mesh, scalars="Field Strength", cmap="rainbow4", show_edges=False, smooth_shading=True)

    plotter.iren.initialize()

    def update_data(step):
        global live_angle
        
        # 1. Non-blocking check for new Redis data
        message = pubsub.get_message(ignore_subscribe_messages=True)
        
        if message and message['type'] == 'message':
            # Extract and parse the tracking angle
            live_angle = float(message['data'].decode('utf-8'))
            print(f"Update: Received Live DOA Angle = {live_angle}°")

        # 2. Map coordinates based on the latest angle
        phi = .5 * np.pi
        theta = np.radians(live_angle)

        x = 3 * np.sin(phi) * np.cos(theta)
        y = 3 * np.sin(phi) * np.sin(theta)
        z = 3 * np.cos(phi)

        rotation_matrix = align_mesh_to_vector([x, y, z], base_axis=(0, 0, 1))
        antenna_actor.user_matrix = rotation_matrix


    # Check for Redis messages every 10 milliseconds (fast tracking loop)
    plotter.add_timer_event(max_steps = 10000000, duration= 10, callback=update_data)

    plotter.show()

if __name__ == "__main__":
    main()
