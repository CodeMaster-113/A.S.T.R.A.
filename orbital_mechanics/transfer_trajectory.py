import math
import numpy as np

def generate_transfer_trajectory(r1, r2, mu, num_points=360):
    r1, r2, mu = float(r1), float(r2), float(mu)
    if min(r1, r2, mu) <= 0 or num_points < 3:
        raise ValueError("Invalid transfer trajectory inputs.")
    a = (r1+r2)/2
    e = abs(r2-r1)/(r2+r1)
    p = a*(1-e*e)
    anomalies = np.linspace(0, math.pi, int(num_points))
    if r2 < r1:
        anomalies = np.linspace(math.pi, 2*math.pi, int(num_points))
    radii = p/(1+e*np.cos(anomalies))
    positions = np.column_stack((radii*np.cos(anomalies), radii*np.sin(anomalies), np.zeros_like(radii)))
    speeds = np.sqrt(mu*(2/radii-1/a))
    velocities = np.column_stack((-np.sin(anomalies)*speeds, (e+np.cos(anomalies))*speeds, np.zeros_like(radii)))
    times = np.linspace(0, math.pi*math.sqrt(a**3/mu), int(num_points))
    return {
        "semi_major_axis": a, "eccentricity": e, "semi_latus_rectum": p,
        "true_anomalies": anomalies, "times": times,
        "positions": positions, "velocities": velocities
    }
