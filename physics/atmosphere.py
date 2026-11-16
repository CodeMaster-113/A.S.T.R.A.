import math

ATMOSPHERE_LAYERS = [
    (0.0, 1.225, 8500.0), (25000.0, 3.899e-2, 6500.0),
    (30000.0, 1.774e-2, 6500.0), (40000.0, 3.972e-3, 7000.0),
    (50000.0, 1.057e-3, 8000.0), (60000.0, 3.206e-4, 7000.0),
    (70000.0, 8.770e-5, 6000.0), (80000.0, 1.905e-5, 5500.0),
    (90000.0, 3.396e-6, 6000.0), (100000.0, 5.297e-7, 7000.0),
    (110000.0, 9.661e-8, 8000.0), (120000.0, 2.438e-8, 10000.0),
    (150000.0, 2.070e-9, 20000.0), (200000.0, 2.789e-10, 30000.0),
    (300000.0, 2.418e-11, 40000.0), (400000.0, 3.725e-12, 50000.0),
    (500000.0, 1.585e-12, 60000.0), (600000.0, 6.967e-13, 70000.0),
    (700000.0, 3.614e-13, 80000.0), (800000.0, 1.454e-13, 90000.0),
    (900000.0, 5.604e-14, 100000.0), (1000000.0, 3.019e-14, 110000.0),
]

def atmospheric_density(altitude):
    altitude = float(altitude)
    if not math.isfinite(altitude) or altitude < 0:
        raise ValueError("Altitude must be finite and nonnegative.")
    for base_altitude, base_density, scale_height in reversed(ATMOSPHERE_LAYERS):
        if altitude >= base_altitude:
            return base_density * math.exp(-(altitude - base_altitude) / scale_height)
    return ATMOSPHERE_LAYERS[0][1]
