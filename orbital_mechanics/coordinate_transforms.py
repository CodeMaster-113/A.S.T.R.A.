import numpy as np

def pqw_to_eci_matrix(inclination, raan, arg_periapsis):
    ci, si = np.cos(inclination), np.sin(inclination)
    co, so = np.cos(raan), np.sin(raan)
    cw, sw = np.cos(arg_periapsis), np.sin(arg_periapsis)
    return np.array([
        [co*cw-so*sw*ci, -co*sw-so*cw*ci, so*si],
        [so*cw+co*sw*ci, -so*sw+co*cw*ci, -co*si],
        [sw*si, cw*si, ci]
    ])

def eci_to_pqw_matrix(inclination, raan, arg_periapsis):
    return pqw_to_eci_matrix(inclination, raan, arg_periapsis).T

def pqw_to_eci(vector, inclination, raan, arg_periapsis):
    return pqw_to_eci_matrix(inclination, raan, arg_periapsis) @ np.asarray(vector, dtype=float)

def eci_to_pqw(vector, inclination, raan, arg_periapsis):
    return eci_to_pqw_matrix(inclination, raan, arg_periapsis) @ np.asarray(vector, dtype=float)
