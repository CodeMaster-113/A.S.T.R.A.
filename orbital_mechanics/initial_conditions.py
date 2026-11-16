import math
import numpy as np
from orbital_mechanics.coordinate_transforms import pqw_to_eci
from orbital_mechanics.orbital_elements import orbital_elements_to_cartesian

def circular_orbit_state(radius, mu, inclination, raan):
    radius, mu = float(radius), float(mu)
    if not math.isfinite(radius) or radius <= 0 or not math.isfinite(mu) or mu <= 0:
        raise ValueError("Radius and mu must be finite and positive.")
    speed = math.sqrt(mu / radius)
    r_pqw = np.array([radius, 0.0, 0.0])
    v_pqw = np.array([0.0, speed, 0.0])
    return (
        pqw_to_eci(r_pqw, inclination, raan, 0.0),
        pqw_to_eci(v_pqw, inclination, raan, 0.0)
    )


def elliptical_orbit_state(
    perigee_radius,
    apogee_radius,
    mu,
    inclination,
    raan=0.0,
    argument_of_periapsis=0.0,
    true_anomaly=0.0
):
    values = (
        perigee_radius, apogee_radius, mu, inclination,
        raan, argument_of_periapsis, true_anomaly
    )
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("Orbital initialization inputs must be finite.")
    rp, ra, mu = map(float, values[:3])
    if rp <= 0 or ra < rp or mu <= 0:
        raise ValueError("Apsis radii must be positive and apogee must not be below perigee.")
    a = (rp + ra) / 2.0
    e = (ra - rp) / (ra + rp)
    if not 0 <= e < 1:
        raise ValueError("Initial orbit must be a bound ellipse.")
    return orbital_elements_to_cartesian(
        a,
        e,
        float(inclination),
        float(raan),
        float(argument_of_periapsis),
        float(true_anomaly),
        mu
    )
