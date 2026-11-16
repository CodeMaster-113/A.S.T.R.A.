import math
import numpy as np
import vispy

vispy.use("pyside6")

from vispy import scene

from PySide6.QtCore import QTimer, QObject, QEvent, Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QPushButton,
    QMessageBox, QGroupBox, QSplitter, QComboBox,
    QFrame, QScrollArea
)

from physics.constants import EARTH_RADIUS, MU_EARTH
from orbital_mechanics.orbital_geometry import (
    orbit_points_from_elements,
    orbit_points_from_state,
)
from orbital_mechanics.orbital_elements import osculating_orbital_elements

from simulation.simulation_manager import SimulationManager

from visualization.earth_renderer import create_earth
from visualization.trajectory_renderer import (
    create_trajectory, update_trajectory
)
from visualization.spacecraft_renderer import (
    create_spacecraft_marker, update_spacecraft_marker
)


# ============================================================
# THEME
# ============================================================

CYAN = "#22d3ee"
AMBER = "#fbbf24"
GREEN = "#34d399"
RED = "#f87171"
TEXT = "#c7d2e0"
DIM = "#64748b"

MONO = (
    '"JetBrains Mono", "Cascadia Mono", "SF Mono", '
    'Consolas, "Courier New", monospace'
)

APP_STYLE = f"""
    QMainWindow, QDialog, QWidget {{
        background-color: #05080f;
        color: {TEXT};
        font-family: {MONO};
        font-size: 12px;
    }}

    QLabel {{
        background: transparent;
        color: {TEXT};
    }}

    QLabel#heading {{
        font-size: 20px;
        font-weight: bold;
        color: {CYAN};
        padding: 10px 14px;
        background-color: #08111d;
        border: 1px solid #14304a;
        border-left: 4px solid {CYAN};
    }}

    QLabel#status {{
        font-weight: bold;
        padding: 6px 14px;
        background-color: #08111d;
        border: 1px solid #14304a;
        border-left: 4px solid {GREEN};
        color: {GREEN};
    }}

    QLabel#dialogTitle {{
        font-size: 20px;
        font-weight: bold;
        color: {CYAN};
        padding: 10px 14px;
        background-color: #08111d;
        border: 1px solid #14304a;
        border-left: 4px solid {CYAN};
    }}

    QLabel#subtitle {{
        color: {DIM};
        padding: 4px 2px 10px 2px;
    }}

    QGroupBox {{
        background-color: #08111d;
        border: 1px solid #14304a;
        border-left: 3px solid {CYAN};
        border-radius: 0px;
        margin-top: 14px;
        padding: 14px 10px 8px 10px;
        font-weight: bold;
        color: {CYAN};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 6px;
        background-color: #05080f;
        color: {CYAN};
    }}

    QLabel#value {{
        color: {CYAN};
        font-weight: bold;
    }}

    QLabel#valueAmber {{
        color: {AMBER};
        font-weight: bold;
    }}

    QLabel#valueGreen {{
        color: {GREEN};
        font-weight: bold;
    }}

    QLabel#planBox {{
        background-color: #060d17;
        border: 1px dashed #1f4468;
        color: {TEXT};
        padding: 10px;
    }}

    QLineEdit, QDoubleSpinBox, QComboBox {{
        background-color: #060d17;
        border: 1px solid #1f3a56;
        border-radius: 0px;
        padding: 5px 8px;
        color: {CYAN};
        selection-background-color: #0e7490;
    }}

    QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 1px solid {CYAN};
    }}

    QDoubleSpinBox::up-button,
    QDoubleSpinBox::down-button {{
        width: 16px;
        background-color: #0c1a2b;
        border-left: 1px solid #1f3a56;
    }}

    QDoubleSpinBox::up-button:hover,
    QDoubleSpinBox::down-button:hover {{
        background-color: #12304d;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 22px;
        background-color: #0c1a2b;
    }}

    QComboBox QAbstractItemView {{
        background-color: #060d17;
        color: {CYAN};
        border: 1px solid #1f3a56;
        selection-background-color: #0e4f6b;
        selection-color: white;
        outline: none;
    }}

    QPushButton {{
        background-color: #0a2740;
        color: {CYAN};
        border: 1px solid {CYAN};
        border-radius: 0px;
        padding: 9px;
        font-weight: bold;
    }}

    QPushButton:hover {{
        background-color: {CYAN};
        color: #021018;
    }}

    QPushButton:pressed {{
        background-color: #0e7490;
        color: white;
    }}

    QPushButton#ghost {{
        background-color: transparent;
        color: {TEXT};
        border: 1px solid #2a4560;
    }}

    QPushButton#ghost:hover {{
        background-color: #12304d;
        color: white;
        border: 1px solid {CYAN};
    }}

    QSplitter::handle {{
        background-color: #14304a;
        width: 2px;
    }}

    QMessageBox QLabel {{
        color: {TEXT};
    }}

    QScrollArea {{
        background: transparent;
        border: none;
    }}

    QScrollBar:vertical {{
        background: #08111d;
        border-left: 1px solid #14304a;
        width: 12px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: #1f4468;
        border: 1px solid #2a5a85;
        min-height: 40px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {CYAN};
        border: 1px solid {CYAN};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
        background: none;
    }}

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background: #08111d;
        border-top: 1px solid #14304a;
        height: 12px;
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background: #1f4468;
        border: 1px solid #2a5a85;
        min-width: 40px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {CYAN};
        border: 1px solid {CYAN};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
        background: none;
    }}

    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {{
        background: none;
    }}
"""


# ============================================================
# WHEEL GUARD
# ============================================================

class WheelGuard(QObject):

    def eventFilter(self, obj, event):

        if (
            event.type() == QEvent.Type.Wheel
            and not obj.hasFocus()
        ):
            event.ignore()
            return True

        return False


# ============================================================
# MISSION INITIALIZATION
# ============================================================

class MissionSetupDialog(QDialog):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "ASTRA | Mission Initialization"
        )

        self.setMinimumWidth(480)
        self.setStyleSheet(APP_STYLE)

        self.configuration = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        title = QLabel("ASTRA MISSION INITIALIZATION")
        title.setObjectName("dialogTitle")

        layout.addWidget(title)

        subtitle = QLabel(
            "Configure spacecraft parameters and initial orbital conditions."
        )

        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(subtitle)

        form_box = QGroupBox(
            "SPACECRAFT CONFIGURATION"
        )

        form = QFormLayout(form_box)
        form.setVerticalSpacing(8)

        self.name = QLineEdit("ASTRA-TEST-01")

        self.net_mass = self._spin(
            0.1, 100000, 60, 2
        )

        self.dry_mass = self._spin(
            0.1, 100000, 50, 2
        )

        self.max_thrust = self._spin(
            0, 100000, 0.8, 3
        )

        self.isp = self._spin(
            1, 10000, 220, 2
        )

        self.cd = self._spin(
            0, 20, 2.2, 3
        )

        self.area = self._spin(
            0, 1000, 0.1, 3
        )

        self.perigee_altitude = self._spin(
            0, 100000, 400, 2
        )

        self.apogee_altitude = self._spin(
            0, 100000, 400, 2
        )

        self.inclination = self._spin(
            0, 180, 30, 2
        )

        self.true_anomaly = self._spin(
            0, 360, 0, 2
        )

        fields = [
            ("Spacecraft name", self.name),
            ("Total mass (kg)", self.net_mass),
            ("Dry mass (kg)", self.dry_mass),
            ("Maximum thrust (N)", self.max_thrust),
            ("Specific impulse (s)", self.isp),
            ("Drag coefficient", self.cd),
            ("Reference area (m²)", self.area),
            ("Initial perigee altitude (km)", self.perigee_altitude),
            ("Initial apogee altitude (km)", self.apogee_altitude),
            ("Initial inclination (°)", self.inclination),
            ("Initial true anomaly (°)", self.true_anomaly)
        ]

        for label, widget in fields:
            form.addRow(label, widget)

        layout.addWidget(form_box)

        button = QPushButton(
            "INITIALIZE MISSION"
        )

        button.clicked.connect(self._validate)

        layout.addWidget(button)

    @staticmethod
    def _spin(lo, hi, value, decimals):

        widget = QDoubleSpinBox()

        widget.setRange(lo, hi)
        widget.setValue(value)
        widget.setDecimals(decimals)

        return widget

    def _validate(self):

        if not self.name.text().strip():

            QMessageBox.warning(
                self,
                "Input error",
                "Enter a spacecraft name."
            )

            return

        if self.dry_mass.value() > self.net_mass.value():

            QMessageBox.warning(
                self,
                "Mass error",
                "Dry mass cannot exceed total mass."
            )

            return

        if self.apogee_altitude.value() < self.perigee_altitude.value():
            QMessageBox.warning(
                self,
                "Orbit error",
                "Initial apogee altitude must be greater than or equal to perigee altitude."
            )
            return

        self.configuration = {
            "name": self.name.text().strip(),
            "net_mass": self.net_mass.value(),
            "dry_mass": self.dry_mass.value(),
            "max_thrust": self.max_thrust.value(),
            "specific_impulse": self.isp.value(),
            "drag_coefficient": self.cd.value(),
            "reference_area": self.area.value(),
            "initial_perigee_altitude_km": self.perigee_altitude.value(),
            "initial_apogee_altitude_km": self.apogee_altitude.value(),
            "inclination_deg": self.inclination.value(),
            "initial_true_anomaly_deg": self.true_anomaly.value()
        }

        self.accept()


# ============================================================
# ORBIT VISUALIZATION GEOMETRY
# ============================================================

def circular_orbit_points(
    radius,
    inclination,
    count=360
):
    return orbit_points_from_elements(
        radius, 0.0, inclination, 0.0, 0.0, MU_EARTH, count
    )


def circular_orbit_from_state(
    position,
    velocity,
    radius,
    count=500
):

    elements = osculating_orbital_elements(position, velocity, MU_EARTH)
    return orbit_points_from_elements(
        radius,
        0.0,
        elements["inclination"],
        elements["raan"],
        elements["argument_of_periapsis"],
        MU_EARTH,
        count
    )


# ============================================================
# OSCULATING ORBIT FROM CURRENT STATE
# ============================================================

def osculating_orbit_points(
    position,
    velocity,
    count=500
):

    return orbit_points_from_state(position, velocity, MU_EARTH, count)


# ============================================================
# MAIN MISSION CONTROL WINDOW
# ============================================================

class MissionWindow(QMainWindow):

    def __init__(self, sim):

        super().__init__()

        self.sim = sim

        self.time_scale = 1.0
        self.simulation_running = True

        # Store the initial fuel amount once.
        # Do not calculate it again from the changing spacecraft mass.

        self.initial_propellant = (
            self.sim.initial_propellant
        )

        self._orbit_refresh_counter = 0
        self._orbit_refresh_interval = 5

        self._transfer_was_active = (
            self.sim.active_transfer is not None
        )
        self._state_version = self.sim.state_version

        self.setWindowTitle(
            "ASTRA | Advanced Orbital Mission Control"
        )

        screen = (
            QApplication.primaryScreen()
            .availableGeometry()
        )

        width = min(
            1650,
            int(screen.width() * 0.94)
        )

        height = min(
            950,
            int(screen.height() * 0.94)
        )

        self.setMinimumSize(900, 560)
        self.resize(width, height)

        self.move(
            screen.x() + (screen.width() - width) // 2,
            screen.y() + (screen.height() - height) // 2
        )

        self.setStyleSheet(APP_STYLE)

        self._build()
        self._build_scene()

        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

        self._telemetry()

    # ========================================================
    # VISUAL CLEANUP
    # ========================================================

    @staticmethod
    def _remove_visual(visual):

        if visual is not None:

            try:
                visual.parent = None
            except Exception:
                pass

    # ========================================================
    # STATUS BAR
    # ========================================================

    def _set_status(self, text, color):

        self.system_status.setText(text)

        self.system_status.setStyleSheet(
            f"color:{color};border-left:4px solid {color};"
        )

    # ========================================================
    # DASHBOARD LAYOUT
    # ========================================================

    def _build(self):

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        heading = QLabel(
            "ASTRA  /  SPACECRAFT MISSION CONTROL"
        )

        heading.setObjectName("heading")
        root.addWidget(heading)

        self.system_status = QLabel(
            "SYSTEM STATUS: INITIALIZING"
        )

        self.system_status.setObjectName("status")
        root.addWidget(self.system_status)

        split = QSplitter()

        # ----------------------------------------------------
        # 3D VIEW
        # ----------------------------------------------------

        self.canvas = scene.SceneCanvas(
            keys="interactive",
            bgcolor="#02040a",
            show=False
        )

        self.view = self.canvas.central_widget.add_view()

        self.view.camera = scene.TurntableCamera(
            fov=45,
            elevation=25,
            azimuth=30,
            distance=18000000
        )

        view_frame = QFrame()

        view_frame.setStyleSheet(
            "QFrame{border:1px solid #14304a;background:#02040a;}"
        )

        vf_layout = QVBoxLayout(view_frame)
        vf_layout.setContentsMargins(1, 1, 1, 1)
        vf_layout.addWidget(self.canvas.native)

        split.addWidget(view_frame)

        # ----------------------------------------------------
        # RIGHT PANEL
        # ----------------------------------------------------

        panel = QWidget()

        pl = QVBoxLayout(panel)
        pl.setContentsMargins(6, 0, 8, 0)
        pl.setSpacing(4)

        self.wheel_guard = WheelGuard(self)

        # ----------------------------------------------------
        # ORBITAL TELEMETRY
        # ----------------------------------------------------

        orbital = QGroupBox(
            "ORBITAL TELEMETRY"
        )

        og = QGridLayout(orbital)

        self.labels = {}

        orbital_fields = [
            ("time", "Mission elapsed time"),
            ("altitude", "Altitude above Earth"),
            ("perigee", "Osculating perigee altitude"),
            ("apogee", "Osculating apogee altitude"),
            ("semi_major_axis", "Semi-major axis"),
            ("eccentricity", "Eccentricity"),
            ("period", "Orbital period"),
            ("radius", "Geocentric radius"),
            ("speed", "Velocity magnitude"),
            ("inclination", "Orbital inclination"),
            ("status", "Orbital status")
        ]

        for row, (key, label) in enumerate(orbital_fields):

            og.addWidget(
                QLabel(label),
                row,
                0
            )

            value = QLabel("--")
            value.setObjectName("value")

            og.addWidget(
                value,
                row,
                1
            )

            self.labels[key] = value

        pl.addWidget(orbital)

        # ----------------------------------------------------
        # POSITION TELEMETRY
        # ----------------------------------------------------

        position_box = QGroupBox(
            "SPACECRAFT POSITION | ECI FRAME"
        )

        pg = QGridLayout(position_box)

        self.position_labels = {}

        for row, axis in enumerate(["X", "Y", "Z"]):

            pg.addWidget(
                QLabel(f"{axis} position"),
                row,
                0
            )

            value = QLabel("--")
            value.setObjectName("valueAmber")

            pg.addWidget(
                value,
                row,
                1
            )

            self.position_labels[axis] = value

        pl.addWidget(position_box)

        # ----------------------------------------------------
        # VELOCITY TELEMETRY
        # ----------------------------------------------------

        velocity_box = QGroupBox(
            "VELOCITY VECTOR | ECI FRAME"
        )

        vg = QGridLayout(velocity_box)

        self.velocity_labels = {}

        for row, axis in enumerate(["Vx", "Vy", "Vz"]):

            vg.addWidget(
                QLabel(axis),
                row,
                0
            )

            value = QLabel("--")
            value.setObjectName("valueGreen")

            vg.addWidget(
                value,
                row,
                1
            )

            self.velocity_labels[axis] = value

        pl.addWidget(velocity_box)

        # ----------------------------------------------------
        # SPACECRAFT HEALTH
        # ----------------------------------------------------

        health = QGroupBox(
            "SPACECRAFT STATUS"
        )

        hf = QFormLayout(health)

        self.labels["mass"] = QLabel("--")
        self.labels["fuel"] = QLabel("--")
        self.labels["fuel_fraction"] = QLabel("--")

        for key in (
            "mass",
            "fuel",
            "fuel_fraction"
        ):
            self.labels[key].setObjectName("value")

        hf.addRow(
            "Current mass",
            self.labels["mass"]
        )

        hf.addRow(
            "Remaining propellant",
            self.labels["fuel"]
        )

        hf.addRow(
            "Propellant fraction",
            self.labels["fuel_fraction"]
        )

        pl.addWidget(health)

        # ----------------------------------------------------
        # SIMULATION SPEED
        # ----------------------------------------------------

        speed_box = QGroupBox(
            "SIMULATION TIME CONTROL"
        )

        sl = QVBoxLayout(speed_box)

        sf = QFormLayout()

        self.speed_selector = QComboBox()

        self.speed_selector.addItems([
            "1x",
            "2x",
            "5x",
            "10x",
            "25x",
            "50x"
        ])

        self.speed_selector.currentTextChanged.connect(
            self._change_speed
        )

        sf.addRow(
            "Simulation speed",
            self.speed_selector
        )

        sl.addLayout(sf)

        self.speed_description = QLabel(
            "1 simulated second per 50 ms."
        )

        self.speed_description.setStyleSheet(
            f"color:{DIM};"
        )

        sl.addWidget(self.speed_description)

        pl.addWidget(speed_box)

        # ----------------------------------------------------
        # ORBIT MANEUVER CONTROL
        # ----------------------------------------------------

        maneuver = QGroupBox(
            "ORBIT MANEUVER CONTROL"
        )

        ml = QVBoxLayout(maneuver)

        mf = QFormLayout()

        self.target_perigee = QDoubleSpinBox()
        self.target_perigee.setRange(0, 100000)
        self.target_perigee.setValue(400)
        self.target_perigee.setDecimals(2)
        self.target_perigee.setSuffix(" km")

        mf.addRow(
            "Target perigee altitude",
            self.target_perigee
        )

        self.target_apogee = QDoubleSpinBox()
        self.target_apogee.setRange(0, 100000)
        self.target_apogee.setValue(800)
        self.target_apogee.setDecimals(2)
        self.target_apogee.setSuffix(" km")

        mf.addRow(
            "Target apogee altitude",
            self.target_apogee
        )

        self.target_inclination = QDoubleSpinBox()

        self.target_inclination.setRange(
            0,
            180
        )

        self.target_inclination.setValue(
            self.sim.initial_inclination
            * 180 / np.pi
        )

        self.target_inclination.setDecimals(3)
        self.target_inclination.setSuffix(" °")

        mf.addRow(
            "Target inclination",
            self.target_inclination
        )

        ml.addLayout(mf)

        self.plan_label = QLabel(
            "No maneuver currently planned."
        )

        self.plan_label.setObjectName("planBox")
        self.plan_label.setWordWrap(True)

        ml.addWidget(self.plan_label)

        execute = QPushButton("EXECUTE APSIDAL TRANSFER")

        execute.clicked.connect(
            self._execute
        )

        ml.addWidget(execute)

        plane_change = QPushButton(
            "EXECUTE INCLINATION CHANGE"
        )

        plane_change.clicked.connect(
            self._execute_inclination_change
        )

        ml.addWidget(plane_change)

        pl.addWidget(maneuver)

        # ----------------------------------------------------
        # SYSTEM CONTROLS
        # ----------------------------------------------------

        self.pause = QPushButton(
            "PAUSE SIMULATION"
        )

        self.pause.setObjectName("ghost")

        self.pause.clicked.connect(
            self._toggle
        )

        pl.addWidget(self.pause)

        reset = QPushButton(
            "RESET CAMERA"
        )

        reset.setObjectName("ghost")

        reset.clicked.connect(
            self._reset_camera
        )

        pl.addWidget(reset)

        pl.addStretch()

        # ----------------------------------------------------
        # WHEEL GUARD
        # ----------------------------------------------------

        for field in (
            self.speed_selector,
            self.target_perigee,
            self.target_apogee,
            self.target_inclination
        ):

            field.setFocusPolicy(
                Qt.FocusPolicy.StrongFocus
            )

            field.installEventFilter(
                self.wheel_guard
            )

        # ----------------------------------------------------
        # SCROLLABLE PANEL
        # ----------------------------------------------------

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        scroll.setMinimumWidth(420)
        scroll.setWidget(panel)

        split.addWidget(scroll)

        split.setCollapsible(0, False)
        split.setCollapsible(1, False)

        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)

        split.setSizes([1150, 500])

        root.addWidget(split, 1)

    # ========================================================
    # 3D SCENE
    # ========================================================

    def _build_scene(self):

        create_earth(self.view.scene)

        # Initial reference orbit: GREEN.
        # This remains fixed as a reference to the initial orbit.

        self.initial_orbit = create_trajectory(
            orbit_points_from_state(
                self.sim.initial_state[:3],
                self.sim.initial_state[3:],
                MU_EARTH
            ),
            self.view.scene,
            (0.2, 0.9, 0.3, 1),
            2
        )

        # Current osculating orbit: ORANGE.
        # This is recalculated from the current state.

        self.current_orbit = None

        # Spacecraft trail: RED.

        self.trail = create_trajectory(
            np.asarray([
                self.sim.get_position()
            ]),
            self.view.scene,
            (1, 0.25, 0.25, 1),
            2
        )

        self.marker = create_spacecraft_marker(
            self.sim.get_position(),
            self.view.scene
        )

        scene.visuals.XYZAxis(
            parent=self.view.scene
        )

        # Target circular orbit: CYAN.

        self.target_line = None

        # Hohmann transfer trajectory: PURPLE.

        self.transfer_line = None

        # Draw the initial current osculating orbit.

        self._refresh_current_orbit()

    # ========================================================
    # CURRENT ORBIT REFRESH
    # ========================================================

    def _refresh_current_orbit(self):

        position = self.sim.get_position()
        velocity = self.sim.get_velocity()

        try:

            points = orbit_points_from_state(
                position,
                velocity,
                MU_EARTH
            )

        except ValueError:

            # If the trajectory becomes unbound, remove
            # the previous elliptical orbit instead of
            # leaving an incorrect stale orbit on screen.

            self._remove_visual(
                self.current_orbit
            )

            self.current_orbit = None

            return

        if self.current_orbit is None:

            self.current_orbit = create_trajectory(
                points,
                self.view.scene,
                (1.0, 0.65, 0.1, 1.0),
                3
            )

        else:

            update_trajectory(
                self.current_orbit,
                points,
                (1.0, 0.65, 0.1, 1.0),
                3
            )

    # ========================================================
    # SIMULATION CLOCK
    # ========================================================

    def _change_speed(self, value):

        self.time_scale = float(
            value.replace("x", "")
        )

        self.speed_description.setText(
            f"{self.time_scale:.0f} simulated seconds per 50 ms."
        )

    def _tick(self):

        try:

            simulated_dt = (
                1.0 * self.time_scale
            )

            self.sim.advance(
                simulated_dt
            )

            self._update_scene()
            self._telemetry()

        except Exception as exc:

            self.timer.stop()

            QMessageBox.critical(
                self,
                "Simulation error",
                str(exc)
            )

    # ========================================================
    # SCENE UPDATE
    # ========================================================

    def _update_scene(self):

        # 1. Update spacecraft marker.

        position = self.sim.get_position()

        update_spacecraft_marker(
            self.marker,
            position
        )

        if self.sim.state_version != self._state_version:
            self._refresh_current_orbit()
            self._orbit_refresh_counter = 0
            self._state_version = self.sim.state_version

        if (
            self.sim.active_transfer is not None
            and self.sim.active_transfer["first_burn_executed"]
            and self.transfer_line is None
        ):
            transfer_points = orbit_points_from_state(
                self.sim.get_position(),
                self.sim.get_velocity(),
                MU_EARTH
            )
            self.transfer_line = create_trajectory(
                transfer_points,
                self.view.scene,
                (0.7, 0.3, 1.0, 1.0),
                2
            )

        # 2. Update spacecraft trail.

        history = np.asarray(
            self.sim.history[-3000:],
            dtype=float
        )

        if (
            history.ndim == 2
            and len(history) >= 2
        ):

            trail_points = history[:, :3]

            update_trajectory(
                self.trail,
                trail_points,
                (1, 0.25, 0.25, 1),
                2
            )

        # 3. Refresh the current osculating orbit periodically.
        # The marker and trail still update every simulation tick.

        self._orbit_refresh_counter += 1

        if (
            self._orbit_refresh_counter
            >= self._orbit_refresh_interval
        ):

            self._refresh_current_orbit()

            self._orbit_refresh_counter = 0

        # 4. Detect completion of the Hohmann transfer.

        transfer_active = (
            self.sim.active_transfer is not None
        )

        if (
            self._transfer_was_active
            and not transfer_active
        ):

            self._remove_visual(
                self.transfer_line
            )

            self.transfer_line = None
            self._remove_visual(self.target_line)
            self.target_line = None

            # Refresh immediately after the second burn.

            self._refresh_current_orbit()

            self._orbit_refresh_counter = 0

            self.plan_label.setText(
                "APSIDAL TRANSFER COMPLETED\n\n"
                "Target apsidal burn executed.\n"
                "Spacecraft has entered its new orbit.\n\n"
                "Current osculating orbit updated."
            )

        self._transfer_was_active = transfer_active

    # ========================================================
    # LIVE TELEMETRY
    # ========================================================

    def _telemetry(self):

        d = self.sim.get_telemetry()

        position = np.asarray(
            d["position"],
            dtype=float
        )

        velocity = np.asarray(
            d["velocity"],
            dtype=float
        )

        # Use the manager's telemetry as the source of truth.

        altitude = d["altitude_km"]
        radius = d["radius_km"]
        speed = np.linalg.norm(velocity)

        inclination = d["inclination_deg"]

        self.labels["time"].setText(
            f'{d["time"]:,.1f} s'
        )

        self.labels["altitude"].setText(
            f"{altitude:.3f} km"
        )

        self.labels["perigee"].setText(
            f'{d["perigee_altitude_km"]:.3f} km'
        )

        apogee = d["apogee_altitude_km"]
        self.labels["apogee"].setText(
            f"{apogee:.3f} km" if math.isfinite(apogee) else "UNBOUND"
        )

        semi_major_axis = d["semi_major_axis_km"]
        self.labels["semi_major_axis"].setText(
            f"{semi_major_axis:.3f} km"
            if math.isfinite(semi_major_axis)
            else "PARABOLIC"
        )

        self.labels["eccentricity"].setText(
            f'{d["eccentricity"]:.7f}'
        )

        period = d["orbital_period_s"]
        self.labels["period"].setText(
            f"{period:,.2f} s" if period is not None else "UNBOUND"
        )

        self.labels["radius"].setText(
            f"{radius:.3f} km"
        )

        self.labels["speed"].setText(
            f"{speed:.3f} m/s"
        )

        self.labels["inclination"].setText(
            f"{inclination:.4f}°"
        )

        self.labels["status"].setText(
            d["maneuver_status"]
        )

        # ----------------------------------------------------
        # ECI POSITION
        # ----------------------------------------------------

        for i, axis in enumerate(["X", "Y", "Z"]):

            self.position_labels[axis].setText(
                f"{position[i]:,.3f} m  |  "
                f"{position[i] / 1000:,.6f} km"
            )

        # ----------------------------------------------------
        # ECI VELOCITY
        # ----------------------------------------------------

        for i, axis in enumerate(["Vx", "Vy", "Vz"]):

            self.velocity_labels[axis].setText(
                f"{velocity[i]:,.6f} m/s"
            )

        # ----------------------------------------------------
        # SPACECRAFT MASS AND PROPELLANT
        # ----------------------------------------------------

        mass = d["mass_kg"]
        fuel = d["propellant_kg"]

        self.labels["mass"].setText(
            f"{mass:.4f} kg"
        )

        self.labels["fuel"].setText(
            f"{fuel:.4f} kg"
        )

        if self.initial_propellant > 0:

            fraction = (
                fuel / self.initial_propellant
            ) * 100.0

        else:

            fraction = 0.0

        fraction = max(
            0.0,
            min(100.0, fraction)
        )

        self.labels["fuel_fraction"].setText(
            f"{fraction:.2f}%"
        )

        # ----------------------------------------------------
        # SYSTEM STATUS
        # ----------------------------------------------------

        if d["transfer_active"]:

            self._set_status(
                "SYSTEM STATUS: MANEUVER EXECUTION",
                AMBER
            )

        else:

            self._set_status(
                "SYSTEM STATUS: NOMINAL ORBITAL OPERATIONS",
                GREEN
            )

    # ========================================================
    # HOHMANN TRANSFER
    # ========================================================

    def _execute(self):

        try:
            plan = self.sim.execute_transfer(
                self.target_perigee.value(),
                self.target_apogee.value()
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Maneuver rejected",
                str(exc)
            )

            return

        try:
            target_points = orbit_points_from_elements(
                plan["target_semi_major_axis"],
                plan["target_eccentricity"],
                plan["target_inclination"],
                plan["target_raan"],
                plan["target_argument_of_periapsis"],
                MU_EARTH
            )

        except ValueError as exc:

            QMessageBox.warning(
                self,
                "Orbit visualization error",
                str(exc)
            )

            self._update_scene()
            self._telemetry()

            return

        self._remove_visual(self.transfer_line)
        self.transfer_line = None
        self._remove_visual(self.target_line)
        self.target_line = None
        if self.sim.active_transfer is not None:
            self.target_line = create_trajectory(
                target_points,
                self.view.scene,
                (0.1, 0.85, 1.0, 1.0),
                2
            )
            if plan["first_burn_executed"]:
                transfer_points = orbit_points_from_state(
                    self.sim.get_position(),
                    self.sim.get_velocity(),
                    MU_EARTH
                )
                self.transfer_line = create_trajectory(
                    transfer_points,
                    self.view.scene,
                    (0.7, 0.3, 1.0, 1.0),
                    2
                )

        self._refresh_current_orbit()
        self._orbit_refresh_counter = 0
        self._update_scene()
        self._telemetry()
        self._state_version = self.sim.state_version

        if plan["single_burn"]:
            self.plan_label.setText(
                "CIRCULARIZATION COMPLETED\n\n"
                f'Burn Δv: {plan["delta_v1"]:.4f} m/s\n'
                f'Propellant required: {plan["propellant_burn1"]:.5f} kg\n'
                "Current osculating orbit updated."
            )
        elif plan["first_burn_pending"]:
            self.plan_label.setText(
                "APSIDAL TRANSFER SCHEDULED\n\n"
                f'Initial perigee: {plan["initial_perigee_altitude_km"]:.3f} km\n'
                f'Initial apogee: {plan["initial_apogee_altitude_km"]:.3f} km\n'
                f'Target perigee: {plan["target_perigee_altitude_km"]:.3f} km\n'
                f'Target apogee: {plan["target_apogee_altitude_km"]:.3f} km\n'
                f'Planned Δv: {plan["total_delta_v"]:.4f} m/s\n'
                f'Propellant: {plan["total_propellant"]:.5f} kg\n\n'
                f'Waiting for {plan["start_apsis"]} to execute the first burn.'
            )
        else:
            self.plan_label.setText(
                "APSIDAL TRANSFER INITIATED\n\n"
                f'First burn Δv: {plan["delta_v1"]:.4f} m/s\n'
                f'Second burn Δv: {plan["delta_v2"]:.4f} m/s\n'
                f'Total Δv: {plan["total_delta_v"]:.4f} m/s\n'
                f'Transfer time: {plan["transfer_time"]:.2f} s\n'
                f'Propellant required: {plan["total_propellant"]:.5f} kg\n\n'
                f'Second burn occurs at the transfer {plan["endpoint_apsis"]}.'
            )

        self._set_status(
            "SYSTEM STATUS: MANEUVER IN PROGRESS"
            if self.sim.active_transfer is not None
            else "SYSTEM STATUS: MANEUVER COMPLETE",
            AMBER if self.sim.active_transfer is not None else GREEN
        )

    # ========================================================
    # ORBITAL PLANE CHANGE
    # ========================================================

    def _execute_inclination_change(self):

        target_deg = (
            self.target_inclination.value()
        )

        try:

            # SimulationManager handles the physical
            # velocity rotation and propellant consumption.

            plan = self.sim.execute_plane_change(
                target_deg
            )

        except Exception as exc:

            QMessageBox.warning(
                self,
                "Plane change rejected",
                str(exc)
            )

            return

        # Obtain the updated spacecraft state.

        position = self.sim.get_position()
        velocity = self.sim.get_velocity()

        try:

            final_points = orbit_points_from_state(
                position,
                velocity,
                MU_EARTH
            )

        except ValueError as exc:

            QMessageBox.warning(
                self,
                "Orbit reconstruction error",
                str(exc)
            )

            self._update_scene()
            self._telemetry()

            return

        # Clear the old target orbit.

        self._remove_visual(
            self.target_line
        )

        self.target_line = None

        # A plane change cannot occur during a transfer,
        # so clear any stale transfer visualization too.

        self._remove_visual(
            self.transfer_line
        )

        self.transfer_line = None

        # Force an immediate current-orbit refresh.

        self._refresh_current_orbit()
        self._orbit_refresh_counter = 0
        self._state_version = self.sim.state_version

        # Update marker, trail and telemetry immediately.

        self._update_scene()
        self._telemetry()

        final_inclination = plan.get(
            "final_inclination_deg",
            self.sim.get_orbital_inclination()
            * 180 / math.pi
        )

        self.plan_label.setText(
            "ORBITAL PLANE CHANGE EXECUTED\n\n"
            f'Initial inclination: '
            f'{plan["initial_inclination_deg"]:.4f}°\n'
            f'Target inclination: '
            f'{plan["target_inclination_deg"]:.4f}°\n'
            f'Final inclination: '
            f'{final_inclination:.4f}°\n'
            f'Plane change Δv: '
            f'{plan["delta_v"]:.4f} m/s\n'
            f'Propellant used: '
            f'{plan["propellant_required"]:.5f} kg\n\n'
            "CURRENT OSCULATING ORBIT UPDATED."
        )

        self._set_status(
            "SYSTEM STATUS: PLANE CHANGE EXECUTED",
            GREEN
        )

    # ========================================================
    # PAUSE / RESUME
    # ========================================================

    def _toggle(self):

        if self.timer.isActive():

            self.timer.stop()

            self.pause.setText(
                "RESUME SIMULATION"
            )

            self.simulation_running = False

            self._set_status(
                "SYSTEM STATUS: SIMULATION PAUSED",
                RED
            )

        else:

            self.timer.start()

            self.pause.setText(
                "PAUSE SIMULATION"
            )

            self.simulation_running = True

            self._set_status(
                "SYSTEM STATUS: SIMULATION RUNNING",
                GREEN
            )

    # ========================================================
    # CAMERA
    # ========================================================

    def _reset_camera(self):

        self.view.camera.center = (
            0,
            0,
            0
        )

        self.view.camera.distance = 18000000
        self.view.camera.elevation = 25
        self.view.camera.azimuth = 30

    # ========================================================
    # SHUTDOWN
    # ========================================================

    def closeEvent(self, event):

        if hasattr(self, "timer"):
            self.timer.stop()

        event.accept()


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def launch_astra():

    app = (
        QApplication.instance()
        or QApplication([])
    )

    setup = MissionSetupDialog()

    if setup.exec() != QDialog.DialogCode.Accepted:
        return

    sim = SimulationManager(
        integration_dt=1.0,
        include_j2=True,
        include_drag=True
    )

    try:

        sim.initialize_spacecraft(
            setup.configuration
        )

    except Exception as exc:

        QMessageBox.critical(
            None,
            "Initialization error",
            str(exc)
        )

        return

    window = MissionWindow(sim)
    window.show()

    app.exec()