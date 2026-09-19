import numpy as np
import matplotlib.pyplot as plt

class HalfMoonCompass:
    def __init__(self, title="Angle Compass"):
        # Turn on interactive mode so updates appear without blocking
        plt.ion()
        # Create a polar axis
        self.fig, self.ax = plt.subplots(subplot_kw={"projection": "polar"})
        self.fig.canvas.manager.set_window_title(title)
        # Put 0° at the top and make positive angles clockwise
        self.ax.set_theta_zero_location("N") # "North" (up) is 0°
        self.ax.set_theta_direction(-1) # clockwise = positive
        # Show only -90° to +90° (half circle)
        self.ax.set_thetamin(-90)
        self.ax.set_thetamax(90)
        # Radius / grid settings (just cosmetic)
        self.ax.set_rmax(1.0)
        self.ax.set_rticks(np.linspace(0.2, 1.0, 5)) # concentric arcs
        self.ax.set_yticklabels([]) # hide radius labels
        self.ax.grid(True)

        # Angle tick labels at -90, -45, 0, 45, 90
        tick_degs = [-90, -45, 0, 45, 90]
        self.ax.set_xticks(np.deg2rad(tick_degs))
        self.ax.set_xticklabels([f"{d}°" for d in tick_degs])
        # Initial needle at 0°
        init_angle = 0.0
        theta = np.deg2rad(init_angle)
        # Needle goes from center (r=0) to edge (r=1)
        (self.needle_line,) = self.ax.plot([theta, theta], [0.0, 1.0], linewidth=3)

        # Text under the compass to show the numeric angle
        self.text = self.ax.text(
            0.5,
            -0.15,
            f"{init_angle:.0f} deg",
            transform=self.ax.transAxes,
            ha="center",
            va="top",
            fontsize=14,
        )

        # Tight layout so the text isn’t cut off
        plt.tight_layout()
        # Draw once
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def update(self, angle_deg):
        """
        Update the compass needle and text.
        angle_deg: angle in degrees, expected in [-90, 90]
        """
        # Clamp angle to the visible range
        angle_deg = max(-90.0, min(90.0, float(angle_deg)))
        theta = np.deg2rad(angle_deg)

        self.needle_line.set_data([theta, theta], [0.0, 1.0])
        self.text.set_text(f"{angle_deg:.0f} deg")
        # Redraw the figure
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

# ----------------------------------------------------------------------
# Demo usage: sweep the needle back and forth if this file is run directly
# ----------------------------------------------------------------------
#demo verified
if __name__ == "__main__":
    compass = HalfMoonCompass(title="Half-Moon Compass Demo")
    # Sweep from -90 to +90
    for a in range(-90, 91, 2):
        compass.update(a)
        plt.pause(0.02)

    # And back from +90 to -90
    for a in range(90, -91, -2):
        compass.update(a)
        plt.pause(0.02)

    # Leave the final plot open in non-interactive mode
    plt.ioff()
    #only needed because there is no autorun in env
    plt.show()