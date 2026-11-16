# ASTRA

**A.S.T.R.A.: A Computational Framework for Spacecraft Orbital Propagation and Trajectory Reconfiguration**

ASTRA is a Python desktop application for exploring Earth-centered spacecraft motion and impulsive orbital maneuvers. It combines a numerical propagator, orbital-element and transfer calculations, a spacecraft/mission model, and a live 3D mission-control interface.

The project is intended for educational use, algorithm exploration, and reproducible simulation experiments. It is not a flight-dynamics qualification tool and should not be used for operational navigation or mission design without independent verification.

## Contents

- [What ASTRA does](#what-astra-does)
- [Capabilities and scope](#capabilities-and-scope)
- [Model and equations](#model-and-equations)
- [Project layout](#project-layout)
- [Requirements and installation](#requirements-and-installation)
- [Run the application](#run-the-application)
- [Use the mission-control interface](#use-the-mission-control-interface)
- [Run the test](#run-the-test)
- [Use the calculation modules](#use-the-calculation-modules)
- [Units and conventions](#units-and-conventions)
- [Scientific limitations](#scientific-limitations)
- [Preparing a paper about ASTRA](#preparing-a-paper-about-astra)
- [Reproducibility checklist](#reproducibility-checklist)
- [Contributing](#contributing)

## What ASTRA does

ASTRA initializes a spacecraft in an Earth-centered elliptical orbit, propagates its Cartesian state, calculates osculating orbital telemetry, and renders the Earth, orbit, spacecraft, and its recent path in a desktop 3D view. A user can schedule an apsidal transfer to new perigee/apogee altitudes or execute an instantaneous inclination change.

The GUI starts each mission with the J2 and atmospheric-drag options enabled. The lower-level simulation classes also allow those effects to be disabled. The propagation is performed in the Earth-centered inertial (ECI) frame using a fixed-step, classical fourth-order Runge–Kutta (RK4) integrator.

## Capabilities and scope

### Implemented

- Initial circular or elliptical, bound Earth orbits, specified by perigee/apogee altitude, inclination, and true anomaly.
- Cartesian state and classical osculating-element conversions, including elliptic, parabolic, and hyperbolic states for element analysis and orbit display.
- Two-body point-mass gravity.
- Optional first-order Earth J2 acceleration.
- Optional atmospheric drag from a piecewise exponential density approximation, with atmospheric co-rotation represented using Earth's rotation rate.
- Fixed-step RK4 state propagation with a shortened final step when needed.
- Spacecraft dry/total mass, maximum thrust and specific impulse parameters, drag coefficient, and reference area.
- Apsidal-transfer planning across candidate starting and destination apsides, followed by burns at the selected apsidal events. Circularization can be completed in one burn.
- Inclination-change planning/execution at the current spacecraft position, with rocket-equation propellant estimation.
- Live telemetry, maneuver status, a bounded recent spacecraft trail, and 3D orbit visualization.
- Standalone Hohmann-transfer and transfer-trajectory calculation utilities.

### Not implemented as a complete physical feature

The equations of motion can include a thrust-acceleration term when thrust is marked active, but the GUI does not expose a continuous-thrust controller, and the propagator does not integrate propellant depletion during continuous thrust. The maneuver workflows currently implemented are idealized instantaneous velocity changes. The `radiation_coefficient` spacecraft property is stored but is not used in the acceleration model.

## Model and equations

### State and reference frame

The propagated state is

`x = [r_x, r_y, r_z, v_x, v_y, v_z]`,

where position is measured in metres and velocity in metres per second in an ECI frame. The dynamics are

`dr/dt = v`

`dv/dt = a_gravity + a_J2 + a_drag + a_thrust`,

with optional accelerations controlled by the simulation environment.

### Gravity and perturbations

The point-mass acceleration is

`a_gravity = -mu_Earth * r / |r|^3`.

When enabled, the J2 term is the standard axisymmetric first-order correction using the configured Earth gravitational parameter, equatorial radius, and J2 coefficient. It is evaluated in the model's fixed z-axis orientation; no higher-order geopotential harmonics are included.

Drag is computed from the velocity relative to a rotating atmosphere:

`v_rel = v - omega_Earth x r`

`a_drag = -(1/2) * rho * Cd * A / m * |v_rel| * v_rel`.

Atmospheric density `rho` is approximated by exponential layers. This is a simplified atmosphere, not a time-, latitude-, longitude-, weather-, or solar-activity-dependent density model.

### Numerical propagation

The `physics.integrator.integrate` routine applies classical RK4 to the six-component state with a fixed maximum step `dt`; the last step is shortened to end exactly at the requested duration. The GUI's `SimulationManager` advances in steps no larger than its configured integration interval and localizes apsidal events by repeatedly propagating and bisecting the event interval.

### Maneuvers

**Apsidal transfer.** The planner evaluates feasible pairs of initial and final apsides, computes the two impulse magnitudes from vis-viva speeds, estimates propellant with the ideal rocket equation, and selects the feasible candidate with the smallest sum of absolute impulse magnitudes. The first burn is executed at the selected initial apsis; the second is executed at the opposite apsis of the transfer orbit. If the destination is circular and the initial burn point already matches the target radius, a single-burn circularization is available. The standalone Hohmann helper in `orbital_mechanics/hohmann_transfer.py` computes the textbook two-impulse transfer between circular radii.

**Inclination change.** The manager constructs a target orbital-plane normal at the current position and rotates the velocity around the local radial axis. The position and speed are preserved by the instantaneous rotation; propellant is estimated from the resulting velocity change. The simplified planner rejects geometrically infeasible requests at the current latitude and rejects a polar position where its construction is undefined.

**Propellant estimate.** For an ideal impulse, the code uses

`m_propellant = m_initial * (1 - exp(-|delta_v| / (Isp * g0)))`.

For a two-burn transfer, the second-burn estimate uses the mass remaining after the first burn.

## Project layout

```text
.
├── main.py                         # Desktop application entry point
├── requirements.txt                # Python runtime dependencies
├── test_plane_change.py            # Standalone plane-change regression test
├── IEEE paper format (1).docx      # Included IEEE-style Word template
├── orbital_mechanics/
│   ├── coordinate_transforms.py    # Perifocal (PQW) and ECI transforms
│   ├── hohmann_transfer.py         # Circular-orbit Hohmann calculations
│   ├── initial_conditions.py       # Initial circular/elliptical states
│   ├── orbital_elements.py         # State/element conversion and osculating elements
│   ├── orbital_geometry.py         # Orbit calculations and geometry points
│   └── transfer_trajectory.py      # Sample planar transfer trajectory
├── physics/
│   ├── atmosphere.py               # Layered exponential density approximation
│   ├── constants.py                # Earth and gravitational constants
│   ├── equation_of_motion.py       # State derivative and acceleration assembly
│   ├── gravity.py                  # Point-mass gravity
│   ├── integrator.py               # Classical RK4 integration
│   ├── pertubations.py             # J2 and atmospheric-drag acceleration
│   └── spacecraft.py               # Spacecraft properties and mass/state
├── simulation/
│   ├── orbit_simulator.py          # Trajectory-oriented simulation wrapper
│   ├── simulation_config.py        # Time-step and environment configuration
│   ├── simulation_manager.py       # Interactive mission state and maneuvers
│   └── trajectory.py               # Time/state history container
└── visualization/
    ├── earth_renderer.py           # Earth sphere
    ├── mission_ui.py               # Setup dialog and mission-control UI
    ├── spacecraft_renderer.py      # Spacecraft marker
    ├── trajectory_renderer.py     # Orbit/trail line visuals
    └── view_orbit.py               # Standalone orbit viewer
```

The module name `pertubations.py` is spelled that way in the source tree; imports should use that spelling unless the file is deliberately renamed along with all callers.

## Requirements and installation

ASTRA requires Python and the packages listed in [`requirements.txt`](requirements.txt):

- NumPy
- PySide6
- VisPy
- PyOpenGL

A working desktop session and graphics/OpenGL support are required to launch the GUI. A virtual environment is recommended.

### Windows PowerShell

From the project directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell prevents environment activation, either use an approved local execution-policy setup or invoke the environment's interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The dependency file specifies minimum versions rather than a fully locked environment. For repeatable experiments, record the Python version, operating system, and exact installed package versions alongside the simulation settings.

## Run the application

From the project root, with the environment activated:

```bash
python main.py
```

On Windows, `py main.py` is also commonly available. The application opens a mission-initialization dialog first. Accepting valid inputs launches the mission-control window; closing or cancelling that dialog exits without starting a mission.

## Use the mission-control interface

### 1. Configure the initial mission

The setup dialog collects:

| Input | Meaning |
|---|---|
| Spacecraft name | Display/identity field for the spacecraft |
| Total mass | Initial spacecraft mass in kg, including propellant |
| Dry mass | Minimum mass in kg; cannot exceed total mass |
| Maximum thrust | Thrust limit in N |
| Specific impulse | Propulsion parameter in seconds |
| Drag coefficient | Dimensionless `Cd` used by the drag model |
| Reference area | Drag area in m² |
| Initial perigee/apogee altitude | Elliptical-orbit apsides above Earth's reference radius, in km |
| Initial inclination | Inclination in degrees |
| Initial true anomaly | Position on the initial orbit, in degrees |

The initial orbit must be an Earth-clear bound ellipse. Set perigee equal to apogee for a circular orbit. In the GUI workflow, RAAN and argument of periapsis use their defaults of zero.

### 2. Read telemetry and the scene

The dashboard displays elapsed time; current altitude and radius; osculating perigee and apogee; semi-major axis, eccentricity, period, and inclination; ECI position and velocity; spacecraft mass and remaining propellant; and current maneuver/orbit status.

The 3D view uses the following visual roles:

- Blue sphere: Earth.
- Green curve: initial reference orbit.
- Orange curve: current osculating orbit.
- Red marker/curve: spacecraft and recent trail.
- Cyan curve: planned target orbit, when displayed.
- Purple curve: transfer orbit, when displayed.

The orbital curves are geometric osculating/conic visualizations. They are not a substitute for the numerical trajectory history.

### 3. Plan or execute a maneuver

- Set the target perigee and apogee altitudes, then select **EXECUTE APSIDAL TRANSFER**. The planner schedules the first burn at the selected current apsis if it is not already there. Simulation advances until the event, propagates through the transfer, and performs the second burn at the other transfer apsis.
- Set the target inclination, then select **EXECUTE INCLINATION CHANGE**. This applies the idealized instantaneous plane change at the current position.
- Maneuvers can be rejected if the target is invalid, an orbit intersects Earth, the requested geometry is not currently feasible, or available propellant is insufficient. The dialog reports the reason.
- **PAUSE SIMULATION** and **RESUME SIMULATION** stop/start the timer. The time-scale selector changes simulated seconds advanced per 50 ms UI timer tick (1x through 50x). **RESET CAMERA** resets the 3D view.

## Run the test

The checked-in standalone test verifies that executing a plane change preserves spacecraft position, preserves speed, changes the orbital inclination to the requested value, consumes the maneuver model correctly, and does not reset elapsed mission time.

```bash
python test_plane_change.py
```

This test imports NumPy and project modules; install the dependencies first. The repository currently contains this standalone test file, not a `tests/` package or a configured test-runner suite.

## Use the calculation modules

The modules can also be imported independently. Inputs to the physics and orbital calculations use SI units unless the function name/signature explicitly indicates altitude in kilometres or angle in degrees.

For example, the standalone circular-orbit transfer helper accepts radii in metres and `mu` in m³/s²:

```python
from physics.constants import MU_EARTH, EARTH_RADIUS
from orbital_mechanics.hohmann_transfer import hohmann_transfer

initial_radius = EARTH_RADIUS + 400_000
target_radius = EARTH_RADIUS + 800_000
plan = hohmann_transfer(initial_radius, target_radius, MU_EARTH)

print(f"Total ideal delta-v: {plan['total_delta_v']:.3f} m/s")
print(f"Transfer time: {plan['transfer_time']:.1f} s")
```

The main interactive API is `simulation.SimulationManager`. It accepts an integration step and the J2/drag switches, then `initialize_spacecraft(config)` initializes the mission. Useful methods include `get_telemetry()`, `calculate_apsidal_transfer(...)`, `execute_transfer(...)`, `calculate_plane_change(...)`, `execute_plane_change(...)`, and `advance(duration_seconds)`. The configuration dictionary keys used by the GUI are defined in `visualization/mission_ui.py`; the initial orbit altitude keys are in km, while spacecraft mass is kg, thrust is N, area is m², and angles are degrees.

## Units and conventions

| Quantity | Unit/convention |
|---|---|
| Position, radius, altitude inside physics calculations | m |
| Velocity | m/s |
| Acceleration | m/s² |
| Time | s |
| Mass / propellant | kg |
| Thrust | N |
| Specific impulse | s |
| Drag coefficient | Dimensionless |
| Reference area | m² |
| Gravitational parameter | m³/s² |
| GUI initial/target altitudes | km above the configured Earth radius |
| GUI and setup orbital angles | degrees; orbital-element functions generally use radians |
| Inertial state coordinates | ECI Cartesian x, y, z |
| Perifocal frame | PQW, transformed to/from ECI by rotation matrices |

The constants are defined in `physics/constants.py`; the implemented values include Earth's gravitational parameter, equatorial radius, J2 coefficient, rotation rate, and standard gravity.

## Scientific limitations

ASTRA is a compact educational simulator. Results depend on the selected time step and simplified environment, and should be treated as model output rather than authoritative predictions.

- Propagation uses a fixed-step, non-adaptive RK4 integrator; no automatic step-size or error control is implemented.
- Earth is represented by a central point-mass term plus optional J2. Other gravity harmonics, third-body effects, solar radiation pressure, tides, and relativistic corrections are absent.
- The atmosphere is a static piecewise exponential approximation; drag accuracy is limited by that model and by fixed spacecraft mass/area/coefficient assumptions.
- Earth orientation is simplified to the z-axis rotation used for atmospheric-relative velocity. No Earth-orientation, precession/nutation, or high-fidelity frame transformations are implemented.
- Maneuvers are ideal instantaneous impulses, with ideal rocket-equation fuel estimates. Finite-duration burns, thrust pointing/control, engine transients, and continuous propellant depletion are not modeled end to end.
- Apsidal transfer planning uses ideal Keplerian transfer speeds even though the simulation can propagate with J2 and drag enabled. Perturbations can therefore make the realized post-maneuver orbit differ from the nominal plan.
- Plane-change planning is tied to the current position and a simplified target-plane construction; it does not search for an optimal maneuver location around the orbit.
- The GUI's time scale changes elapsed simulated time per timer tick; it does not refine the integration time step.
- No benchmark results, formal error bounds, flight-software qualification, or comparison against an independent high-fidelity reference are provided in this repository.

For serious use, independently validate equations, constants, coordinate/frame conventions, event handling, conservation behavior, and convergence with respect to time step.

## Preparing a paper about ASTRA

The repository includes [`IEEE paper format (1).docx`](IEEE%20paper%20format%20%281%29.docx), an IEEE-style conference Word template. It contains formatting instructions and sample/template text, not a completed scientific paper or validated experimental results. Replace all placeholder abstract, keywords, captions, sample references, and template prose. Confirm the current conference's own author instructions before submission because requirements can differ from this template.

The title already present in the template is:

> **A.S.T.R.A.: A Computational Framework for Spacecraft Orbital Propagation and Trajectory Reconfiguration**

The file also contains draft author/affiliation details. Verify the author list, spelling, institution, corresponding-author contact, consent to publish contact information, and conference requirements before submission.

### Paper-format notes from the included template

The supplied Word document describes an A4, two-column layout, with a 4.22 mm inter-column gap and these margins: top 19 mm, bottom 43 mm, and left/right 14.32 mm. It specifies Times New Roman or Times, justified and indented body paragraphs, no page numbers/headers/footers, and no more than three heading levels. Its sample sizing calls for a 24 pt title, 11 pt author names, 10 pt body and headings, 9 pt abstract body, and 8 pt captions/references. These values summarize the included template; the target conference's current submission rules take precedence.

### Recommended paper structure

1. **Title, authors, affiliations, and abstract.** State the specific contribution, implemented model, evaluation method, and measured results. Do not claim accuracy or novelty unless the experiments support it.
2. **Keywords.** For example: orbital mechanics, spacecraft simulation, numerical integration, Hohmann transfer, orbital maneuver, spacecraft visualization. Keep only terms that match the actual paper.
3. **Introduction.** Define the educational/research problem, explain the need for an interactive propagation-and-maneuver environment, summarize relevant prior work, and state a narrow, verifiable contribution.
4. **Related work and theory.** Cite authoritative orbital-mechanics, numerical-analysis, atmospheric-drag, and Earth-gravity sources. Distinguish ASTRA's implementation from established equations and existing tools.
5. **System architecture.** Explain the separation among orbital mechanics, physics, simulation, and visualization modules. Include a block diagram or data-flow figure if useful.
6. **Mathematical and numerical model.** Define the ECI state, units, gravitational parameter and other constants, point-mass/J2/drag terms, atmosphere assumptions, RK4 update, integration step, apsidal event detection, maneuver equations, and fuel calculation.
7. **Implementation.** Report Python and dependency versions, platform/graphics environment, initialization and simulation workflow, configuration values, and the role of the GUI. Identify which features are fully implemented and which are not.
8. **Experimental method.** State research questions, test cases, initial conditions, environment switches, time steps, comparison references, run counts, measured quantities, and how error or convergence is calculated. Make each experiment repeatable from the repository.
9. **Results.** Present measured—not anticipated—results, with units, appropriate precision, uncertainty/error definitions, and comparisons. Include figures/tables that directly answer the research questions.
10. **Discussion and limitations.** Interpret observed behavior, explain discrepancies, discuss sensitivity to time step and perturbations, and identify model limitations.
11. **Conclusion and future work.** Summarize evidence-backed findings and specific next steps without implying that proposed features already exist.
12. **Acknowledgment and references.** Acknowledge contributors/funding as applicable and cite every external model, constant source, algorithm, library, and figure.

### Abstract drafting scaffold

Use this only as a structure to fill with the actual study; replace every bracket and do not leave unsupported claims in the final paper:

> This paper presents ASTRA, [specific purpose/contribution]. The system combines [implemented dynamics and numerical method] with [implemented maneuver and visualization capabilities]. We evaluated it using [test cases and independent reference], with [time steps, duration, and perturbation settings]. Results show [measured result with units and error/uncertainty]. The findings indicate [limited conclusion supported by those measurements], while [most important limitation] remains.

The paper should include actual numerical results before the abstract is completed. A project description or successful GUI launch alone is not evidence of dynamical accuracy.

### Experiments that could support a paper

These are recommended study designs, not results already established by the repository:

- **Two-body propagation check:** disable J2 and drag; propagate a known elliptical orbit; compare energy, angular momentum, orbital period, and state against analytic/independent reference values.
- **Integrator convergence:** repeat the same scenario with progressively smaller RK4 steps; report state error and invariant drift versus step size and runtime.
- **Hohmann transfer check:** compare the standalone helper and manager plan against independently calculated vis-viva/transfer values for multiple radius pairs. Clearly separate analytical plan values from the perturbed propagated trajectory.
- **Apsidal event/maneuver check:** report requested versus achieved target apsides, burn timing, delta-v, propellant, and numerical sensitivity, with J2/drag settings stated.
- **Plane-change check:** test several initial/target inclinations and orbital locations, documenting the cases rejected because the simplified geometry is infeasible.
- **Perturbation sensitivity:** compare matched runs with J2 and/or drag enabled and disabled; report the exact altitude, spacecraft parameters, duration, and atmosphere assumptions.
- **Software verification:** describe automated test coverage and any additional tests added for the paper. The existing plane-change test alone does not establish overall simulator accuracy.

For every figure/table, state whether it displays analytic calculations, simulated values, or both. Include the integration step and model switches in captions or methods when they affect interpretation.

### Claims and evidence

Avoid unsupported claims such as “high fidelity,” “flight ready,” “optimal trajectory,” or “validated” unless a defined validation study supports them. The manager selects the lowest-total-`delta-v` candidate among its enumerated apsidal-transfer options; this is not a general optimal-control solution. Label assumptions and approximations in the abstract, methods, results, and conclusions.

## Reproducibility checklist

For each published experiment, preserve and report:

- Repository revision/commit or archived source snapshot.
- Python version, operating system, CPU/GPU if relevant, and package versions.
- Initial state or all initialization inputs (including mass, perigee/apogee, inclination, true anomaly, and any non-default angles).
- Integration time step, simulated duration, and whether J2 and drag were enabled.
- Maneuver request, planned and realized burn details, and initial propellant.
- Constants and atmosphere assumptions, with source citations in the paper.
- Exact output quantities, comparison source, error metric, and plotting/data-processing procedure.
- Any random seeds if stochastic behavior is introduced in future versions.

Record measurements from actual runs; this README and the IEEE template do not supply simulation data or performance claims.

## Contributing

Keep changes focused, preserve explicit unit conventions, and add targeted tests when changing numerical behavior. Before proposing results for publication, run the available regression test and add independent numerical checks appropriate to the changed model. Document new assumptions and any changes to maneuver, propagation, or GUI behavior here.

## License

No license file is currently included in this repository. Do not assume the source is licensed for redistribution or reuse; add and review an explicit license before publishing or accepting external contributions.
