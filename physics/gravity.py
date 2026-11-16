import math
import numpy as np

def gravitational_acceleration(position, mu):
    position = np.asarray(position, dtype=float)
    mu = float(mu)
    if position.shape != (3,) or not np.all(np.isfinite(position)):
        raise ValueError("Position must contain 3 finite values.")
    if not math.isfinite(mu) or mu <= 0:
        raise ValueError("mu must be finite and positive.")
    radius = np.linalg.norm(position)
    if radius == 0:
        raise ValueError("Position cannot be zero.")
    return -mu * position / radius**3
