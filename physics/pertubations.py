import numpy as np
from physics import constants as con

def j2_acceleration(pos, mu):
    pos = np.asarray(pos, dtype=float)
    if pos.shape != (3,) or not np.all(np.isfinite(pos)):
        raise ValueError("Position must contain 3 finite values.")
    x, y, z = pos
    r = np.linalg.norm(pos)
    if r == 0:
        raise ValueError("Position cannot be zero.")
    factor = (3 * con.EARTH_J2 * float(mu) * con.EARTH_RADIUS**2) / (2 * r**5)
    return factor * np.array([
        x * (5*z*z/r**2 - 1),
        y * (5*z*z/r**2 - 1),
        z * (5*z*z/r**2 - 3)
    ])

def atmospheric_drag(pos, vel, mass, cd, area, rho):
    pos = np.asarray(pos, dtype=float)
    vel = np.asarray(vel, dtype=float)
    mass, cd, area, rho = map(float, (mass, cd, area, rho))
    if pos.shape != (3,) or vel.shape != (3,):
        raise ValueError("Position and velocity must each contain 3 values.")
    if not np.all(np.isfinite(pos)) or not np.all(np.isfinite(vel)):
        raise ValueError("Position and velocity must be finite.")
    if mass <= 0 or cd < 0 or area < 0 or rho < 0:
        raise ValueError("Invalid drag parameters.")
    omega = np.array([0.0, 0.0, con.EARTH_ROTATION_RATE])
    relative_velocity = vel - np.cross(omega, pos)
    speed = np.linalg.norm(relative_velocity)
    return -0.5 * rho * cd * area / mass * speed * relative_velocity
