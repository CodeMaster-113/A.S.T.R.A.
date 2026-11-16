import math
import numpy as np
from physics.atmosphere import atmospheric_density
from physics.constants import EARTH_RADIUS
from physics.gravity import gravitational_acceleration
from physics.pertubations import atmospheric_drag, j2_acceleration

def state_derivative(state, spacecraft, environment=None, mu=None):
    state = np.asarray(state, dtype=float)
    if state.shape != (6,) or not np.all(np.isfinite(state)):
        raise ValueError("State must contain 6 finite values.")
    environment = environment or {"include_j2": False, "include_drag": False}
    if not isinstance(environment, dict):
        raise TypeError("Environment must be a dictionary.")
    if mu is None:
        mu = environment.get("mu")
    if mu is None or not math.isfinite(float(mu)) or float(mu) <= 0:
        raise ValueError("A finite positive gravitational parameter is required.")
    position, velocity = state[:3], state[3:]
    acceleration = gravitational_acceleration(position, float(mu))
    if environment.get("include_j2", False):
        acceleration += j2_acceleration(position, float(mu))
    if environment.get("include_drag", False):
        altitude = np.linalg.norm(position) - EARTH_RADIUS
        if altitude >= 0:
            rho = environment.get("atmospheric_density", atmospheric_density)(altitude)
            acceleration += atmospheric_drag(
                position, velocity, spacecraft.net_mass,
                spacecraft.drag_coefficient, spacecraft.reference_area, rho
            )
    if getattr(spacecraft, "thrust_active", False):
        direction = np.asarray(spacecraft.thrust_direction, dtype=float)
        norm = np.linalg.norm(direction)
        thrust = float(spacecraft.thrust_magnitude)
        if direction.shape != (3,) or not np.all(np.isfinite(direction)) or norm == 0:
            raise ValueError("Invalid thrust direction.")
        if not math.isfinite(thrust) or thrust < 0 or thrust > spacecraft.max_thrust:
            raise ValueError("Invalid thrust magnitude.")
        acceleration += (thrust * direction / norm) / spacecraft.net_mass
    return np.concatenate((velocity, acceleration))

def equations_of_motion(dt, state, spacecraft, mu, environment=None):
    dt = float(dt)
    if not math.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive.")
    return np.asarray(state, dtype=float) + state_derivative(state, spacecraft, environment, mu) * dt
