import math
import numpy as np
from physics.constants import EARTH_RADIUS

from orbital_mechanics.orbital_elements import (
    orbital_elements_to_cartesian,
    osculating_orbital_elements,
)

def validate_elliptical_orbit(a, e, mu):
    if not all(math.isfinite(float(x)) for x in (a, e, mu)):
        raise ValueError("Orbit parameters must be finite.")
    if a <= 0 or not 0 <= e < 1 or mu <= 0:
        raise ValueError("Invalid elliptical orbit parameters.")

def semi_latus_rectum(a, e):
    validate_elliptical_orbit(a, e, 1.0)
    return a * (1.0 - e**2)

def periapsis_radius(a, e):
    validate_elliptical_orbit(a, e, 1.0)
    return a * (1.0 - e)

def apoapsis_radius(a, e):
    validate_elliptical_orbit(a, e, 1.0)
    return a * (1.0 + e)

def orbital_period(a, mu):
    if a <= 0 or mu <= 0:
        raise ValueError("a and mu must be positive.")
    return 2.0 * math.pi * math.sqrt(a**3 / mu)

def orbital_radius(a, e, true_anomaly):
    validate_elliptical_orbit(a, e, 1.0)
    return a * (1-e**2) / (1 + e*math.cos(true_anomaly))

def orbital_speed(r, mu, a):
    if r <= 0 or mu <= 0 or a <= 0:
        raise ValueError("r, mu and a must be positive.")
    value = mu * (2.0/r - 1.0/a)
    if value < 0:
        raise ValueError("Invalid radius for this orbit.")
    return math.sqrt(value)

def specific_orbital_energy(a, mu):
    if a <= 0 or mu <= 0:
        raise ValueError("a and mu must be positive.")
    return -mu / (2*a)

def specific_angular_momentum(a, e, mu):
    validate_elliptical_orbit(a, e, mu)
    return math.sqrt(mu*a*(1-e**2))

def flight_path_angle(e, true_anomaly):
    if not 0 <= e < 1:
        raise ValueError("Eccentricity must be in [0, 1).")
    return math.atan2(e*math.sin(true_anomaly), 1+e*math.cos(true_anomaly))


def orbit_points_from_elements(a, e, inclination, raan, arg_periapsis,
                               mu, count=500):
    if count < 3:
        raise ValueError("At least three orbit points are required.")
    if not 0 <= float(e) < 1:
        raise ValueError("Closed orbit geometry requires an elliptical orbit.")
    anomalies = np.linspace(0.0, 2.0 * math.pi, int(count))
    return np.asarray([
        orbital_elements_to_cartesian(
            a, e, inclination, raan, arg_periapsis, anomaly, mu
        )[0]
        for anomaly in anomalies
    ])


def orbit_points_from_state(position, velocity, mu, count=500):
    """Create the current osculating conic geometry from an ECI state."""
    if count < 3:
        raise ValueError("At least three trajectory points are required.")
    elements = osculating_orbital_elements(position, velocity, mu)
    e = elements["eccentricity"]
    hvec = elements["angular_momentum_vector"]
    h_hat = hvec / np.linalg.norm(hvec)
    evec = elements["eccentricity_vector"]
    if e > 1e-10:
        p_hat = evec / e
    else:
        r = np.asarray(position, dtype=float)
        p_hat = r / np.linalg.norm(r)
    q_hat = np.cross(h_hat, p_hat)
    q_hat /= np.linalg.norm(q_hat)
    p = elements["specific_angular_momentum"] ** 2 / mu

    if elements["conic_type"] == "elliptic":
        anomalies = np.linspace(0.0, 2.0 * math.pi, int(count))
    else:
        radius = float(np.linalg.norm(position))
        max_radius = max(
            radius * 4.0,
            elements["periapsis_radius"] * 10.0,
            6.0 * EARTH_RADIUS,
        )
        cosine_limit = (p / max_radius - 1.0) / max(e, 1e-12)
        max_anomaly = math.acos(float(np.clip(cosine_limit, -1.0, 1.0)))
        if e > 1.0:
            max_anomaly = min(max_anomaly, math.acos(-1.0 / e) - 1e-6)
        anomalies = np.linspace(-max_anomaly, max_anomaly, int(count))

    denominator = 1.0 + e * np.cos(anomalies)
    valid = denominator > 0.0
    radii = p / denominator[valid]
    anomalies = anomalies[valid]
    return radii[:, None] * (
        np.cos(anomalies)[:, None] * p_hat
        + np.sin(anomalies)[:, None] * q_hat
    )
