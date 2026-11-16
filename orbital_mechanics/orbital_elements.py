import math
import numpy as np

from orbital_mechanics.coordinate_transforms import pqw_to_eci


_TOL = 1e-10


def osculating_orbital_elements(position, velocity, mu):
    """Return classical osculating elements for any non-radial conic."""
    rvec = np.asarray(position, dtype=float)
    vvec = np.asarray(velocity, dtype=float)
    mu = float(mu)
    if (
        rvec.shape != (3,)
        or vvec.shape != (3,)
        or not np.all(np.isfinite(rvec))
        or not np.all(np.isfinite(vvec))
    ):
        raise ValueError("Position and velocity must each contain 3 finite values.")
    if not math.isfinite(mu) or mu <= 0:
        raise ValueError("Gravitational parameter must be finite and positive.")

    radius = float(np.linalg.norm(rvec))
    speed = float(np.linalg.norm(vvec))
    if radius <= 0:
        raise ValueError("Position cannot be zero.")

    hvec = np.cross(rvec, vvec)
    h = float(np.linalg.norm(hvec))
    if h <= _TOL:
        raise ValueError("Radial trajectories do not have a defined orbital plane.")

    nvec = np.cross((0.0, 0.0, 1.0), hvec)
    n = float(np.linalg.norm(nvec))
    evec = np.cross(vvec, hvec) / mu - rvec / radius
    eccentricity = float(np.linalg.norm(evec))
    energy = speed * speed / 2.0 - mu / radius
    inclination = math.acos(float(np.clip(hvec[2] / h, -1.0, 1.0)))

    if n > _TOL:
        raan = math.atan2(nvec[1], nvec[0]) % (2 * math.pi)
    else:
        raan = 0.0

    if eccentricity > _TOL:
        if n > _TOL:
            argp = math.atan2(
                np.dot(np.cross(nvec, evec), hvec) / (n * eccentricity * h),
                np.dot(nvec, evec) / (n * eccentricity),
            )
        else:
            argp = math.atan2(
                evec[1],
                evec[0],
            )
        true_anomaly = math.atan2(
            np.dot(np.cross(evec, rvec), hvec) / (eccentricity * radius * h),
            np.dot(evec, rvec) / (eccentricity * radius),
        )
    else:
        argp = 0.0
        reference = nvec / n if n > _TOL else np.array(
            [0.0, 0.0, math.copysign(1.0, hvec[2])]
        )
        true_anomaly = math.atan2(
            np.dot(np.cross(reference, rvec), hvec) / (radius * h),
            np.dot(reference, rvec) / radius,
        )

    if energy < -_TOL:
        semi_major_axis = -mu / (2.0 * energy)
        conic_type = "elliptic"
    elif energy > _TOL:
        semi_major_axis = -mu / (2.0 * energy)
        conic_type = "hyperbolic"
    else:
        semi_major_axis = math.inf
        conic_type = "parabolic"

    periapsis_radius = h * h / mu / (1.0 + eccentricity)
    apoapsis_radius = (
        semi_major_axis * (1.0 + eccentricity)
        if conic_type == "elliptic"
        else math.inf
    )
    period = (
        2.0 * math.pi * math.sqrt(semi_major_axis**3 / mu)
        if conic_type == "elliptic"
        else None
    )

    return {
        "semi_major_axis": semi_major_axis,
        "eccentricity": eccentricity,
        "inclination": inclination,
        "raan": raan,
        "argument_of_periapsis": argp % (2 * math.pi),
        "true_anomaly": true_anomaly % (2 * math.pi),
        "specific_orbital_energy": energy,
        "specific_angular_momentum": h,
        "angular_momentum_vector": hvec,
        "eccentricity_vector": evec,
        "periapsis_radius": periapsis_radius,
        "apoapsis_radius": apoapsis_radius,
        "orbital_period": period,
        "conic_type": conic_type,
    }


def cartesian_to_orbital_elements(position, velocity, mu):
    """Return ``(a, e, i, raan, argp, true_anomaly)`` for a bound orbit."""
    elements = osculating_orbital_elements(position, velocity, mu)
    if elements["conic_type"] != "elliptic":
        raise ValueError("Only bound elliptical orbits have a finite semi-major axis.")
    return (
        elements["semi_major_axis"],
        elements["eccentricity"],
        elements["inclination"],
        elements["raan"],
        elements["argument_of_periapsis"],
        elements["true_anomaly"],
    )


def orbital_elements_to_cartesian(
    a, e, inclination, raan, arg_periapsis, true_anomaly, mu
):
    a, e, mu = float(a), float(e), float(mu)
    angles = (inclination, raan, arg_periapsis, true_anomaly)
    if (
        not all(math.isfinite(float(value)) for value in (a, e, mu, *angles))
        or a <= 0
        or not 0 <= e < 1
        or mu <= 0
    ):
        raise ValueError("Invalid elliptical orbit parameters.")
    p = a * (1.0 - e * e)
    denominator = 1.0 + e * math.cos(true_anomaly)
    if denominator <= 0:
        raise ValueError("True anomaly is outside the elliptical orbit.")
    radius = p / denominator
    r_pqw = np.array([radius * math.cos(true_anomaly), radius * math.sin(true_anomaly), 0.0])
    v_pqw = math.sqrt(mu / p) * np.array(
        [-math.sin(true_anomaly), e + math.cos(true_anomaly), 0.0]
    )
    return (
        pqw_to_eci(r_pqw, inclination, raan, arg_periapsis),
        pqw_to_eci(v_pqw, inclination, raan, arg_periapsis),
    )
