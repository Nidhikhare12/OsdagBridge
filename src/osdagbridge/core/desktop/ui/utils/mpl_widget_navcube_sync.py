"""
Bridges a Matplotlib FigureCanvasQTAgg (with an Axes3D) to a NavCubeOverlay.
Mirrors the OCCNavCubeSync pattern exactly.

Usage:
    sync = MatplotlibNavCubeSync(canvas, navicube)
    sync.force_sync()   # push camera immediately (call after update_plot)
    sync.teardown()     # call on widget close
"""
import math
from PySide6.QtCore import QTimer


def _get_3d_ax(canvas):
    from mpl_toolkits.mplot3d import Axes3D
    for ax in canvas.figure.axes:
        if isinstance(ax, Axes3D):
            return ax
    return None


def _elev_azim_to_inward(elev_deg, azim_deg):
    elev = math.radians(elev_deg)
    azim = math.radians(azim_deg)
    return math.cos(elev) * math.cos(azim), math.cos(elev) * math.sin(azim), math.sin(elev)


def _inward_to_elev_azim(dx, dy, dz):
    mag = math.sqrt(dx*dx + dy*dy + dz*dz)
    if mag < 1e-10:
        return 30.0, -60.0
    dx, dy, dz = dx/mag, dy/mag, dz/mag
    return math.degrees(math.asin(max(-1.0, min(1.0, dz)))), math.degrees(math.atan2(dy, dx))


def _up_vector(dx, dy, dz, roll_deg=0.0):
    ref = (1.0, 0.0, 0.0) if abs(dz) > 0.999 else (0.0, 0.0, 1.0)
    dot = ref[0]*dx + ref[1]*dy + ref[2]*dz
    ux, uy, uz = ref[0]-dot*dx, ref[1]-dot*dy, ref[2]-dot*dz
    m = math.sqrt(ux*ux + uy*uy + uz*uz)
    if m < 1e-10:
        return 0.0, 0.0, 1.0
    ux, uy, uz = ux/m, uy/m, uz/m
    if abs(roll_deg) < 0.01:
        return ux, uy, uz
    c, s = math.cos(math.radians(roll_deg)), math.sin(math.radians(roll_deg))
    cx, cy, cz = dy*uz-dz*uy, dz*ux-dx*uz, dx*uy-dy*ux
    return ux*c+cx*s, uy*c+cy*s, uz*c+cz*s


class MatplotlibNavCubeSync:
    _TICK_MS = 50

    def __init__(self, canvas, navicube):
        self._canvas   = canvas
        self._navicube = navicube
        self._last     = (None, None, None)

        navicube.viewOrientationRequested.connect(self._on_orientation_requested)

        self._tmr = QTimer()
        self._tmr.timeout.connect(self._tick)
        self._tmr.start(self._TICK_MS)

    def set_interaction_active(self, active: bool):
        if self._navicube:
            self._navicube.set_interaction_active(active)

    def force_sync(self):
        self._last = (None, None, None)
        self._tick()

    def teardown(self):
        self._tmr.stop()
        try:
            if self._navicube:
                self._navicube.viewOrientationRequested.disconnect(self._on_orientation_requested)
        except Exception:
            pass
        self._canvas = self._navicube = None

    def _tick(self):
        if not self._canvas or not self._navicube:
            return
        ax = _get_3d_ax(self._canvas)
        if ax is None:
            return
        try:
            elev = float(ax.elev)
            azim = float(ax.azim)
            roll = float(getattr(ax, "roll", 0.0))
        except Exception:
            return
        if (elev, azim, roll) == self._last:
            return
        self._last = (elev, azim, roll)
        dx, dy, dz = _elev_azim_to_inward(elev, azim)
        ux, uy, uz = _up_vector(dx, dy, dz, roll)
        try:
            self._navicube.push_camera(dx, dy, dz, ux, uy, uz)
        except Exception:
            pass

    def _on_orientation_requested(self, px, py, pz, ux, uy, uz):
        if not self._canvas:
            return
        ax = _get_3d_ax(self._canvas)
        if ax is None:
            return
        elev, azim = _inward_to_elev_azim(-px, -py, -pz)
        try:
            ax.view_init(elev=elev, azim=azim, roll=0)
            self._canvas.draw_idle()
            self._last = (None, None, None)
        except Exception:
            pass