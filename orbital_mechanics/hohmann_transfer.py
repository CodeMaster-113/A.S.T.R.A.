import math

def hohmann_transfer(r1, r2, mu):
    r1, r2, mu = float(r1), float(r2), float(mu)
    if not all(math.isfinite(x) for x in (r1, r2, mu)) or min(r1, r2, mu) <= 0:
        raise ValueError("Radii and mu must be finite and positive.")
    if math.isclose(r1, r2, rel_tol=0, abs_tol=1e-9):
        raise ValueError("Initial and target radii are equal.")
    a = (r1+r2)/2
    vc1, vc2 = math.sqrt(mu/r1), math.sqrt(mu/r2)
    vt1 = math.sqrt(mu*(2/r1-1/a))
    vt2 = math.sqrt(mu*(2/r2-1/a))
    dv1, dv2 = vt1-vc1, vc2-vt2
    tof = math.pi*math.sqrt(a**3/mu)
    return {
        "transfer_semi_major_axis": a,
        "initial_circular_speed": vc1,
        "target_circular_speed": vc2,
        "transfer_speed_at_initial": vt1,
        "transfer_speed_at_target": vt2,
        "delta_v1": dv1,
        "delta_v2": dv2,
        "total_delta_v": abs(dv1)+abs(dv2),
        "transfer_time": tof
    }
