"""
Authors: 
    Jon Kraft, Nov 5 2022

Maintainers:
    Aidan Hsu, Sep 16 2026
    Matthew Comeau, Sep 16 2026

View Original on Github:
    https://github.com/jonkraft/Pluto_Beamformer
    video walkthrough of this [original] at: https://www.youtube.com/@jonkraft

View [Sep 16 2026] on Github:

"""
# Copyright (C) 2020 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# - Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in
# the documentation and/or other materials provided with the
# distribution.
# - Neither the name of Analog Devices, Inc. nor the names of its
# contributors may be used to endorse or promote products derived
# from this software without specific prior written permission.
# - The use of this software may or may not infringe the patent rights
# of one or more patent holders. This license does not release you
# from the requirement that you obtain separate licenses from these
# patent holders to use this software.
# - Use of the software either in source or binary form, must be run
# on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# Copyright (C) 2020 Analog Devices, Inc.
#
# All rights reserved.

"""
Combined single-process beamformer app.

Merges find_theta.py (Pluto monopulse tracker + tracking plot),
half_moon_compass.py (compass) and 3d_monopulse_track.py (3D antenna pattern)
into one Qt window. Redis is no longer needed.

The SDR runs in a worker QThread so the GUI stays responsive. The worker
sends the tracked angle to the GUI through a Qt signal.

Extra dependency:  pip install pyvistaqt
Needs radii.csv and plot_mesh.ply in the same folder as this script
(or the current working directory).
"""
import sys
import time
from pathlib import Path

import adi
import numpy as np
import pyqtgraph as pg
import pyvista as pv
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from pyqtgraph.Qt import QtCore, QtWidgets
from pyvistaqt import QtInteractor

'''Setup'''
samp_rate = 2e6  # must be <=30.72 MHz if both channels are enabled
NumSamples = 2**12
rx_lo = 900e6
rx_mode = "manual"  # can be "manual" or "slow_attack"
rx_gain0 = 40
rx_gain1 = 40
tx_lo = rx_lo
tx_gain = -3
fc0 = int(200e3)
INITIAL_PHASE_CAL = -100
tracking_length = 1000
GUI_UPDATE_PERIOD = 0.03  # seconds between GUI updates (~33 fps)

''' Set distance between Rx antennas '''
d_wavelength = 0.5  # distance between elements as a fraction of wavelength
wavelength = 3E8 / rx_lo
d = d_wavelength * wavelength
print("Set distance between Rx Antennas to ", int(d * 1000), "mm")

ts = 1 / float(samp_rate)
signal_start = int(NumSamples * (samp_rate / 2 + fc0 / 2) / samp_rate)
signal_end = int(NumSamples * (samp_rate / 2 + fc0 * 2) / samp_rate)


def find_file(name):
    """Look next to this script first, then in the current directory."""
    here = Path(__file__).resolve().parent / name
    return str(here if here.exists() else Path(name))


# ----------------------------------------------------------------------------
# Signal processing helpers (unchanged from find_theta.py)
# ----------------------------------------------------------------------------
def calc_theta(phase):
    # steering angle for a given phase delta (deg): theta = arcsin(c*dphi/(2*pi*f*d))
    arcsin_arg = np.deg2rad(phase) * 3E8 / (2 * np.pi * rx_lo * d)
    arcsin_arg = max(min(1, arcsin_arg), -1)
    return np.rad2deg(np.arcsin(arcsin_arg))


def dbfs(raw_data):
    # IQ samples -> FFT, scaled in dBFS
    n = len(raw_data)
    win = np.hamming(n)
    y = raw_data * win
    s_fft = np.fft.fft(y) / np.sum(win)
    s_shift = np.fft.fftshift(s_fft)
    s_dbfs = 20 * np.log10(np.abs(s_shift) / (2**11))  # 12-bit signed ADC
    return s_shift, s_dbfs


def monopulse_angle(array1, array2):
    # correlate the sum and delta signals around the fc0 bins
    corr = np.correlate(array1[signal_start:signal_end],
                        array2[signal_start:signal_end], 'valid')
    return np.angle(corr)


# ----------------------------------------------------------------------------
# SDR worker (runs in its own thread)
# ----------------------------------------------------------------------------
class PlutoTracker(QtCore.QObject):
    angle_updated = QtCore.Signal(float)  # tracked angle in degrees
    status = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.phase_cal = INITIAL_PHASE_CAL
        self.delay = 0
        self._running = True
        self._reset_requested = False
        self._cal_requested = False

        '''Create and configure the Pluto'''
        self.sdr = sdr = adi.ad9361(uri='ip:192.168.2.1')
        sdr.rx_enabled_channels = [0, 1]
        sdr.sample_rate = int(samp_rate)
        sdr.rx_rf_bandwidth = int(fc0 * 3)
        sdr.rx_lo = int(rx_lo)
        sdr.gain_control_mode = rx_mode
        sdr.rx_hardwaregain_chan0 = int(rx_gain0)
        sdr.rx_hardwaregain_chan1 = int(rx_gain1)
        sdr.rx_buffer_size = int(NumSamples)
        sdr._rxadc.set_kernel_buffers_count(1)  # avoid stale data
        sdr.tx_rf_bandwidth = int(fc0 * 3)
        sdr.tx_lo = int(rx_lo)
        sdr.tx_cyclic_buffer = True
        sdr.tx_hardwaregain_chan0 = int(tx_gain)
        sdr.tx_hardwaregain_chan1 = int(-88)
        sdr.tx_buffer_size = int(2**18)

        '''Program Tx and send data'''
        fs = int(sdr.sample_rate)
        N = 2**16
        t = np.arange(0, N * (1 / float(fs)), 1 / float(fs))
        iq0 = (np.cos(2 * np.pi * t * fc0) + 1j * np.sin(2 * np.pi * t * fc0)) * 2 ** 14
        sdr.tx([iq0, iq0])

    # --- requests from the GUI thread (just set flags; the loop acts on them) ---
    def request_reset(self):
        self._reset_requested = True

    def request_calibrate(self):
        self._cal_requested = True

    def stop(self):
        self._running = False

    # --- DSP ---
    def _scan_for_doa(self):
        data = self.sdr.rx()
        rx_0, rx_1 = data[0], data[1]
        peak_sum = []
        delay_phases = np.arange(-180, 180, 2)
        for phase_delay in delay_phases:
            delayed_rx_1 = rx_1 * np.exp(1j * np.deg2rad(phase_delay + self.phase_cal))
            _, sum_dbfs = dbfs(rx_0 + delayed_rx_1)
            peak_sum.append(np.max(sum_dbfs))
        return delay_phases[int(np.argmax(peak_sum))]

    def _track_step(self, last_delay):
        data = self.sdr.rx()
        rx_0, rx_1 = data[0], data[1]
        delayed_rx_1 = rx_1 * np.exp(1j * np.deg2rad(last_delay + self.phase_cal))
        sum_fft, _ = dbfs(rx_0 + delayed_rx_1)
        delta_fft, _ = dbfs(rx_0 - delayed_rx_1)
        mono = float(np.ravel(monopulse_angle(sum_fft, delta_fft))[0])
        phase_step = 1
        return last_delay - phase_step if np.sign(mono) > 0 else last_delay + phase_step

    def _initial_scan(self):
        self.status.emit("Scanning for direction of arrival...")
        for _ in range(20):  # let Pluto run for a bit, to do all its calibrations
            self.sdr.rx()
        self.delay = self._scan_for_doa()
        self.status.emit(f"Tracking (DOA {int(calc_theta(self.delay))}°, "
                         f"phase_cal {self.phase_cal:.0f}°)")

    def run(self):
        self._initial_scan()
        last_emit = 0.0
        while self._running:
            if self._reset_requested:
                self._reset_requested = False
                self._initial_scan()
            if self._cal_requested:
                self._cal_requested = False
                self.phase_cal += self.delay  # fold current offset into the calibration
                self.delay = 0
                print("Calibrated: phase_cal =", self.phase_cal, "deg")
                self.status.emit(f"Calibrated: phase_cal = {self.phase_cal:.0f}°")

            self.delay = self._track_step(self.delay)

            now = time.monotonic()
            if now - last_emit >= GUI_UPDATE_PERIOD:
                last_emit = now
                self.angle_updated.emit(float(calc_theta(self.delay)))


# ----------------------------------------------------------------------------
# Half-moon compass, embedded as a Qt widget
# ----------------------------------------------------------------------------
class CompassWidget(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        fig = Figure(figsize=(4, 3))
        super().__init__(fig)
        self.setParent(parent)
        self.ax = fig.add_subplot(111, projection="polar")
        self.ax.set_theta_zero_location("N")  # 0° at the top
        self.ax.set_theta_direction(-1)       # clockwise = positive
        self.ax.set_thetamin(-90)
        self.ax.set_thetamax(90)
        self.ax.set_rmax(1.0)
        self.ax.set_rticks(np.linspace(0.2, 1.0, 5))
        self.ax.set_yticklabels([])
        self.ax.grid(True)
        tick_degs = [-90, -45, 0, 45, 90]
        self.ax.set_xticks(np.deg2rad(tick_degs))
        self.ax.set_xticklabels([f"{t}°" for t in tick_degs])
        (self.needle,) = self.ax.plot([0, 0], [0.0, 1.0], linewidth=3)
        self.text = self.ax.text(0.5, -0.15, "0 deg", transform=self.ax.transAxes,
                                 ha="center", va="top", fontsize=14)
        fig.tight_layout()

    def update_angle(self, angle_deg):
        angle_deg = max(-90.0, min(90.0, float(angle_deg)))
        theta = np.deg2rad(angle_deg)
        self.needle.set_data([theta, theta], [0.0, 1.0])
        self.text.set_text(f"{angle_deg:.0f} deg")
        self.draw_idle()


# ----------------------------------------------------------------------------
# 3D antenna pattern, embedded with pyvistaqt
# ----------------------------------------------------------------------------
def align_mesh_to_vector(target_vector):
    """4x4 matrix that points the +Z axis toward target_vector."""
    target = np.array(target_vector, dtype=float)
    norm = np.linalg.norm(target)
    if norm == 0:
        return np.eye(4)
    z_prime = target / norm
    tmp = np.array([1.0, 0.0, 0.0]) if abs(z_prime[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x_prime = np.cross(tmp, z_prime)
    x_prime /= np.linalg.norm(x_prime)
    y_prime = np.cross(z_prime, x_prime)
    mat = np.eye(4)
    mat[:3, 0] = x_prime
    mat[:3, 1] = y_prime
    mat[:3, 2] = z_prime
    return mat


class AntennaView:
    def __init__(self, parent=None):
        self.plotter = QtInteractor(parent)
        self.widget = self.plotter.interactor
        self._build_scene()

    def _build_scene(self):
        plotter = self.plotter
        r_max = 3.0
        phi_rad = np.radians(np.linspace(0, 360, 16, endpoint=False))
        angles_deg = np.degrees(phi_rad)

        # radial reference lines
        for rad in phi_rad:
            plotter.add_mesh(pv.Line((0, 0, 0), (r_max * np.cos(rad), r_max * np.sin(rad), 0)),
                             color='royalblue', opacity=0.5, line_width=1)
            plotter.add_mesh(pv.Line((0, 0, 0), (r_max * np.cos(rad), 0, r_max * np.sin(rad))),
                             color='crimson', opacity=0.5, line_width=1)

        # azimuth (phi) labels, equatorial plane
        r_label = r_max * 1.15
        phi_points = np.column_stack([r_label * np.cos(phi_rad), r_label * np.sin(phi_rad),
                                      np.zeros_like(phi_rad)])
        plotter.add_point_labels(phi_points, [f"phi = {int(a)}°" for a in angles_deg],
                                 font_size=12, text_color="royalblue",
                                 shape_opacity=0, always_visible=True)

        # elevation (theta) labels, vertical plane
        theta_points = np.column_stack([r_label * np.cos(phi_rad), np.zeros_like(phi_rad),
                                        r_label * np.sin(phi_rad)])
        plotter.add_point_labels(theta_points, [f"theta = {int(a)}°" for a in angles_deg],
                                 font_size=12, text_color="crimson",
                                 shape_opacity=0, always_visible=True)

        # reference rings
        meridian = pv.Circle(radius=r_max, resolution=64)
        meridian.rotate_x(90, inplace=True)
        plotter.add_mesh(meridian, style='wireframe', color='crimson', opacity=0.5, line_width=1.5)
        plotter.add_mesh(pv.Circle(radius=r_max, resolution=64), style='wireframe',
                         color='royalblue', opacity=0.5, line_width=1.5)

        # antenna pattern mesh
        radii = np.loadtxt(find_file("radii.csv"), delimiter=",")
        mesh = pv.read(find_file("plot_mesh.ply"))
        mesh = mesh.scale(3.5, inplace=False)
        mesh = mesh.rotate_z(90, inplace=False)
        mesh["Field Strength"] = radii.ravel(order='F')
        self.antenna_actor = plotter.add_mesh(mesh, scalars="Field Strength", cmap="rainbow4",
                                              show_edges=False, smooth_shading=True)

    def set_angle(self, angle_deg):
        phi = 0.5 * np.pi
        theta = np.radians(angle_deg)
        vec = [3 * np.sin(phi) * np.cos(theta),
               3 * np.sin(phi) * np.sin(theta),
               3 * np.cos(phi)]
        self.antenna_actor.user_matrix = align_mesh_to_vector(vec)
        self.plotter.render()

    def close(self):
        self.plotter.close()


# ----------------------------------------------------------------------------
# Main window
# ----------------------------------------------------------------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monopulse Beamformer")
        self.resize(1400, 800)

        # tracking trace (line across the plot when tracking begins)
        self.tracking_angles = self._blank_trace()

        # --- widgets ---
        self.antenna_view = AntennaView(self)
        self.compass = CompassWidget(self)

        self.plot = pg.PlotWidget()
        p1 = self.plot.getPlotItem()
        p1.setXRange(-80, 80)
        p1.setYRange(0, tracking_length)
        p1.setLabel('bottom', 'Steering Angle', 'deg', **{'color': '#FFF', 'size': '14pt'})
        p1.showAxis('left', show=False)
        p1.showGrid(x=True, alpha=1)
        p1.setTitle('Monopulse Tracking: Angle vs Time', **{'color': '#FFF', 'size': '14pt'})
        font = QtWidgets.QApplication.font()
        font.setPointSize(15)
        p1.getAxis("bottom").setTickFont(font)
        self.curve = p1.plot(self.tracking_angles)

        btn_reset = QtWidgets.QPushButton("Reset")
        btn_cal = QtWidgets.QPushButton("Center at 0°")
        self.status_label = QtWidgets.QLabel("Starting...")

        # --- layout: 3D on the left; plot over compass on the right; buttons below ---
        right = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        right.addWidget(self.plot)
        right.addWidget(self.compass)
        right.setSizes([450, 350])

        top = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        top.addWidget(self.antenna_view.widget)
        top.addWidget(right)
        top.setSizes([800, 600])

        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(btn_reset)
        buttons.addWidget(btn_cal)
        buttons.addWidget(self.status_label, stretch=1)

        central = QtWidgets.QWidget()
        outer = QtWidgets.QVBoxLayout(central)
        outer.addWidget(top, stretch=1)
        outer.addLayout(buttons)
        self.setCentralWidget(central)

        # --- SDR worker thread ---
        self.tracker = PlutoTracker()
        self.thread = QtCore.QThread()
        self.tracker.moveToThread(self.thread)
        self.thread.started.connect(self.tracker.run)
        self.tracker.angle_updated.connect(self.on_angle)
        self.tracker.status.connect(self.status_label.setText)
        btn_reset.clicked.connect(self.on_reset)
        btn_cal.clicked.connect(self.tracker.request_calibrate)
        self.thread.start()

    @staticmethod
    def _blank_trace():
        trace = np.ones(tracking_length) * 180
        trace[:-1] = -180
        return trace

    def on_angle(self, angle):
        self.tracking_angles = np.append(self.tracking_angles, angle)[1:]
        self.curve.setData(self.tracking_angles, np.arange(tracking_length))
        self.compass.update_angle(angle)
        self.antenna_view.set_angle(angle)

    def on_reset(self):
        self.tracking_angles = self._blank_trace()
        self.tracker.request_reset()

    def closeEvent(self, event):
        self.tracker.stop()
        self.thread.quit()
        self.thread.wait(5000)
        try:
            self.tracker.sdr.tx_destroy_buffer()
        except Exception as e:
            print(f"tx_destroy_buffer failed: {e}")
        self.antenna_view.close()
        super().closeEvent(event)


if __name__ == '__main__':
    app = pg.mkQApp("Monopulse Beamformer")
    window = MainWindow()
    window.show()
    pg.exec()