import math
import numpy as np

from physics.constants import MU_EARTH, EARTH_RADIUS, G0
from physics.spacecraft import Spacecraft
from physics.integrator import integrate
from orbital_mechanics.initial_conditions import elliptical_orbit_state
from orbital_mechanics.orbital_elements import osculating_orbital_elements


class SimulationManager:
    def __init__(self, integration_dt=1.0, include_j2=True, include_drag=True):
        self.integration_dt = float(integration_dt)
        if not math.isfinite(self.integration_dt) or self.integration_dt <= 0:
            raise ValueError("integration_dt must be positive.")

        self.spacecraft = None
        self.initial_state = None
        self.current_state = None
        self.elapsed_time = 0.0
        self.initial_perigee_altitude = None
        self.initial_apogee_altitude = None
        self.initial_altitude = None
        self.initial_inclination = None
        self.initial_propellant = 0.0
        self.history = []
        self.environment = {
            "include_j2": bool(include_j2),
            "include_drag": bool(include_drag),
            "mu": MU_EARTH,
        }
        self.active_transfer = None
        self.last_maneuver = None
        self.state_version = 0

    def _check(self):
        if self.spacecraft is None or self.current_state is None:
            raise RuntimeError("Initialize spacecraft first.")

    def initialize_spacecraft(self, cfg):
        if "initial_perigee_altitude_km" in cfg:
            perigee_altitude = float(cfg["initial_perigee_altitude_km"]) * 1000.0
            apogee_altitude = float(
                cfg.get("initial_apogee_altitude_km", cfg["initial_perigee_altitude_km"])
            ) * 1000.0
        else:
            perigee_altitude = float(cfg["initial_altitude_km"]) * 1000.0
            apogee_altitude = perigee_altitude
        inclination = math.radians(float(cfg["inclination_deg"]))
        true_anomaly = math.radians(float(cfg.get("initial_true_anomaly_deg", 0.0)))
        raan = math.radians(float(cfg.get("raan_deg", 0.0)))
        argp = math.radians(float(cfg.get("argument_of_periapsis_deg", 0.0)))

        orbital_inputs = (
            perigee_altitude, apogee_altitude, inclination,
            true_anomaly, raan, argp
        )
        if not all(math.isfinite(value) for value in orbital_inputs):
            raise ValueError("Initial orbital inputs must be finite.")
        if not 0 <= true_anomaly <= 2.0 * math.pi:
            raise ValueError("Initial true anomaly must be between 0 and 360 degrees.")
        if perigee_altitude < 0:
            raise ValueError("Initial perigee altitude cannot be below Earth's surface.")
        if apogee_altitude < perigee_altitude:
            raise ValueError("Initial apogee altitude must be greater than or equal to perigee altitude.")
        if not 0 <= inclination <= math.pi:
            raise ValueError("Inclination must be between 0 and 180 degrees.")
        if perigee_altitude + EARTH_RADIUS < EARTH_RADIUS:
            raise ValueError("Initial orbit intersects Earth.")

        rp = EARTH_RADIUS + perigee_altitude
        ra = EARTH_RADIUS + apogee_altitude
        eccentricity = (ra - rp) / (ra + rp)
        if not 0 <= eccentricity < 1:
            raise ValueError("Initial orbit must have eccentricity less than 1.")

        position, velocity = elliptical_orbit_state(
            rp, ra, MU_EARTH, inclination, raan, argp, true_anomaly
        )
        state = np.concatenate((position, velocity)).astype(float)

        self.spacecraft = Spacecraft(
            cfg["name"],
            cfg["net_mass"],
            cfg["dry_mass"],
            state,
            cfg["max_thrust"],
            cfg["specific_impulse"],
            cfg["drag_coefficient"],
            cfg["reference_area"],
        )
        self.initial_state = state.copy()
        self.current_state = state.copy()
        self.initial_perigee_altitude = perigee_altitude
        self.initial_apogee_altitude = apogee_altitude
        self.initial_altitude = perigee_altitude
        self.initial_inclination = inclination
        self.initial_propellant = self.spacecraft.get_remaining_propellant()
        self.elapsed_time = 0.0
        self.history = [state.copy()]
        self.active_transfer = None
        self.last_maneuver = None
        self.state_version = 0
        return self.spacecraft

    def get_position(self):
        self._check()
        return self.current_state[:3].copy()

    def get_velocity(self):
        self._check()
        return self.current_state[3:].copy()

    def get_altitude(self):
        return float(np.linalg.norm(self.get_position()) - EARTH_RADIUS)

    def get_speed(self):
        return float(np.linalg.norm(self.get_velocity()))

    def _propellant_for_dv(self, dv, mass=None):
        self._check()
        sc = self.spacecraft
        if sc.specific_impulse <= 0:
            raise RuntimeError("Specific impulse must be positive.")
        dv = abs(float(dv))
        initial_mass = sc.net_mass if mass is None else float(mass)
        used = initial_mass * (1.0 - math.exp(-dv / (sc.specific_impulse * G0)))
        available = sc.get_remaining_propellant()
        if mass is None and used > available + 1e-10:
            raise RuntimeError(
                f"Insufficient propellant: need {used:.4f} kg, have {available:.4f} kg."
            )
        return float(used)

    def get_orbital_elements(self):
        self._check()
        return osculating_orbital_elements(
            self.current_state[:3], self.current_state[3:], MU_EARTH
        )

    def get_orbital_inclination(self):
        return self.get_orbital_elements()["inclination"]

    @staticmethod
    def _rotate_vector(vector, axis, angle):
        vector = np.asarray(vector, dtype=float)
        axis = np.asarray(axis, dtype=float)
        axis_norm = np.linalg.norm(axis)
        if axis_norm < 1e-12:
            raise ValueError("Rotation axis cannot be zero.")
        axis = axis / axis_norm
        return (
            vector * math.cos(angle)
            + np.cross(axis, vector) * math.sin(angle)
            + axis * np.dot(axis, vector) * (1.0 - math.cos(angle))
        )

    def calculate_plane_change(self, target_inclination_deg):
        self._check()
        if self.active_transfer is not None:
            raise RuntimeError("Cannot change inclination during an active apsidal transfer.")
        target_deg = float(target_inclination_deg)
        if not math.isfinite(target_deg) or not 0 <= target_deg <= 180:
            raise ValueError("Target inclination must be between 0 and 180 degrees.")

        target_i = math.radians(target_deg)
        position = self.current_state[:3].copy()
        velocity = self.current_state[3:].copy()
        r_norm = np.linalg.norm(position)
        if r_norm < 1e-12:
            raise RuntimeError("Invalid spacecraft position.")
        r_hat = position / r_norm
        h = np.cross(position, velocity)
        h_norm = np.linalg.norm(h)
        if h_norm < 1e-12:
            raise RuntimeError("Cannot determine current orbital plane.")

        current_normal = h / h_norm
        current_i = math.acos(np.clip(current_normal[2], -1.0, 1.0))
        rho = np.linalg.norm(position[:2])
        if rho < 1e-8:
            raise RuntimeError(
                "Plane change is undefined at this polar position in the simplified planner."
            )

        latitude = math.atan2(position[2], rho)
        radial_horizontal = np.array([position[0] / rho, position[1] / rho, 0.0])
        transverse_horizontal = np.array([-position[1] / rho, position[0] / rho, 0.0])
        cos_i, sin_i = math.cos(target_i), math.sin(target_i)
        a = -math.tan(latitude) * cos_i
        b_squared = sin_i**2 - a**2
        if b_squared < -1e-10:
            raise ValueError(
                "Target inclination is not geometrically possible at the current spacecraft latitude. "
                "Continue simulation to another orbital position."
            )
        b = math.sqrt(max(0.0, b_squared))
        candidates = (
            a * radial_horizontal + b * transverse_horizontal + np.array([0.0, 0.0, cos_i]),
            a * radial_horizontal - b * transverse_horizontal + np.array([0.0, 0.0, cos_i]),
        )
        target_normal = max(candidates, key=lambda candidate: np.dot(current_normal, candidate))
        target_normal = target_normal / np.linalg.norm(target_normal)
        rotation_angle = math.atan2(
            np.dot(r_hat, np.cross(current_normal, target_normal)),
            np.dot(current_normal, target_normal),
        )
        new_velocity = self._rotate_vector(velocity, r_hat, rotation_angle)
        delta_v_vector = new_velocity - velocity
        delta_v = float(np.linalg.norm(delta_v_vector))
        propellant_required = self._propellant_for_dv(delta_v)
        return {
            "initial_inclination_deg": math.degrees(current_i),
            "target_inclination_deg": target_deg,
            "rotation_angle_deg": math.degrees(rotation_angle),
            "delta_v": delta_v,
            "delta_v_vector": delta_v_vector.copy(),
            "propellant_required": propellant_required,
            "initial_normal": current_normal.copy(),
            "target_normal": target_normal.copy(),
            "initial_position": position.copy(),
            "initial_velocity": velocity.copy(),
            "final_velocity": new_velocity.copy(),
        }

    def execute_plane_change(self, target_inclination_deg):
        plan = self.calculate_plane_change(target_inclination_deg)
        self.spacecraft.consume_propellant(plan["propellant_required"])
        self.current_state[3:] = plan["final_velocity"].copy()
        self.spacecraft.set_states(self.current_state)
        self.history.append(self.current_state.copy())
        self.state_version += 1
        plan["final_inclination_deg"] = math.degrees(self.get_orbital_inclination())
        self.last_maneuver = {
            "type": "PLANE CHANGE",
            "time": self.elapsed_time,
            "delta_v": plan["delta_v"],
            "final_inclination_deg": plan["final_inclination_deg"],
        }
        return plan

    @staticmethod
    def _apsis_radial_speed(state):
        position = state[:3]
        radius = np.linalg.norm(position)
        return float(np.dot(position, state[3:]) / radius)

    def _apsis_event_is_here(self, apsis_type):
        if abs(self._apsis_radial_speed(self.current_state)) > 1e-5:
            return False
        elements = self.get_orbital_elements()
        radius = float(np.linalg.norm(self.current_state[:3]))
        expected = (
            elements["periapsis_radius"]
            if apsis_type == "perigee"
            else elements["apoapsis_radius"]
        )
        return abs(radius - expected) <= max(1e-3, expected * 1e-10)

    def _fuel_for_sequence(self, dv1, dv2):
        mass = self.spacecraft.net_mass
        fuel1 = self._propellant_for_dv(dv1, mass)
        fuel2 = self._propellant_for_dv(dv2, mass - fuel1)
        if fuel1 + fuel2 > self.spacecraft.get_remaining_propellant() + 1e-10:
            raise RuntimeError("Insufficient propellant for both transfer burns.")
        return fuel1, fuel2

    def calculate_apsidal_transfer(
        self, target_perigee_altitude_km, target_apogee_altitude_km
    ):
        self._check()
        if self.active_transfer is not None:
            raise RuntimeError("A transfer is already in progress.")

        target_perigee_altitude = float(target_perigee_altitude_km) * 1000.0
        target_apogee_altitude = float(target_apogee_altitude_km) * 1000.0
        if not all(math.isfinite(x) for x in (
            target_perigee_altitude, target_apogee_altitude
        )):
            raise ValueError("Target altitudes must be finite.")
        if target_perigee_altitude < 0:
            raise ValueError("Target perigee altitude cannot be below Earth's surface.")
        if target_apogee_altitude < target_perigee_altitude:
            raise ValueError("Target apogee altitude must be greater than or equal to target perigee altitude.")

        current = self.get_orbital_elements()
        if current["conic_type"] != "elliptic":
            raise ValueError("Apsidal transfer requires a bound elliptical starting orbit.")
        if current["periapsis_radius"] < EARTH_RADIUS:
            raise ValueError("Current osculating orbit intersects Earth.")
        rp_target = EARTH_RADIUS + target_perigee_altitude
        ra_target = EARTH_RADIUS + target_apogee_altitude
        target_e = (ra_target - rp_target) / (ra_target + rp_target)
        if not 0 <= target_e < 1:
            raise ValueError("Target orbit must be a bound ellipse.")
        if (
            math.isclose(current["periapsis_radius"], rp_target, abs_tol=1e-3)
            and math.isclose(current["apoapsis_radius"], ra_target, abs_tol=1e-3)
        ):
            raise ValueError("Target orbit is already achieved.")
        start_apsides = [
            ("perigee", current["periapsis_radius"]),
            ("apogee", current["apoapsis_radius"]),
        ]
        if current["eccentricity"] <= 1e-10:
            start_apsides = [("perigee", current["semi_major_axis"])]
        target_apsides = [("perigee", rp_target), ("apogee", ra_target)]
        candidates = []

        for start_type, start_radius in start_apsides:
            start_speed = math.sqrt(
                MU_EARTH * (2.0 / start_radius - 1.0 / current["semi_major_axis"])
            )
            for endpoint_type, endpoint_radius in target_apsides:
                # Equal-endpoint cases are handled as a single-impulse circularization below.
                if math.isclose(start_radius, endpoint_radius, abs_tol=1e-4):
                    if math.isclose(rp_target, ra_target, abs_tol=1e-4):
                        target_speed = math.sqrt(MU_EARTH / endpoint_radius)
                        dv = target_speed - start_speed
                        fuel, _ = self._fuel_for_sequence(dv, 0.0)
                        candidates.append({
                            "start_apsis": start_type,
                            "endpoint_apsis": endpoint_type,
                            "start_radius": start_radius,
                            "endpoint_radius": endpoint_radius,
                            "transfer_semi_major_axis": start_radius,
                            "transfer_eccentricity": 0.0,
                            "delta_v1": dv,
                            "delta_v2": 0.0,
                            "transfer_time": 0.0,
                            "propellant_burn1": fuel,
                            "propellant_burn2": 0.0,
                            "single_burn": True,
                        })
                    continue
                transfer_perigee = min(start_radius, endpoint_radius)
                transfer_apogee = max(start_radius, endpoint_radius)
                if transfer_perigee < EARTH_RADIUS:
                    continue
                a_transfer = 0.5 * (start_radius + endpoint_radius)
                e_transfer = (
                    transfer_apogee - transfer_perigee
                ) / (transfer_apogee + transfer_perigee)
                transfer_speed1 = math.sqrt(
                    MU_EARTH * (2.0 / start_radius - 1.0 / a_transfer)
                )
                transfer_speed2 = math.sqrt(
                    MU_EARTH * (2.0 / endpoint_radius - 1.0 / a_transfer)
                )
                target_a = 0.5 * (rp_target + ra_target)
                target_speed2 = math.sqrt(
                    MU_EARTH * (2.0 / endpoint_radius - 1.0 / target_a)
                )
                dv1 = transfer_speed1 - start_speed
                dv2 = target_speed2 - transfer_speed2
                try:
                    fuel1, fuel2 = self._fuel_for_sequence(dv1, dv2)
                except RuntimeError:
                    continue
                candidates.append({
                    "start_apsis": start_type,
                    "endpoint_apsis": endpoint_type,
                    "start_radius": start_radius,
                    "endpoint_radius": endpoint_radius,
                    "transfer_semi_major_axis": a_transfer,
                    "transfer_eccentricity": e_transfer,
                    "delta_v1": dv1,
                    "delta_v2": dv2,
                    "transfer_time": math.pi * math.sqrt(a_transfer**3 / MU_EARTH),
                    "propellant_burn1": fuel1,
                    "propellant_burn2": fuel2,
                    "single_burn": False,
                })

        if not candidates:
            raise ValueError(
                "No Earth-clear, propellant-feasible two-impulse apsidal transfer is available."
            )
        best = min(candidates, key=lambda item: (
            abs(item["delta_v1"]) + abs(item["delta_v2"])
        ))
        return {
            **best,
            "initial_perigee_radius": current["periapsis_radius"],
            "initial_apogee_radius": current["apoapsis_radius"],
            "initial_radius": best["start_radius"],
            "initial_altitude_km": (
                best["start_radius"] - EARTH_RADIUS
            ) / 1000.0,
            "initial_perigee_altitude_km": (
                current["periapsis_radius"] - EARTH_RADIUS
            ) / 1000.0,
            "initial_apogee_altitude_km": (
                current["apoapsis_radius"] - EARTH_RADIUS
            ) / 1000.0,
            "initial_semi_major_axis": current["semi_major_axis"],
            "initial_eccentricity": current["eccentricity"],
            "initial_inclination_deg": math.degrees(current["inclination"]),
            "initial_true_anomaly_deg": math.degrees(current["true_anomaly"]),
            "initial_argument_of_periapsis_deg": math.degrees(
                current["argument_of_periapsis"]
            ),
            "target_perigee_radius": rp_target,
            "target_apogee_radius": ra_target,
            "target_perigee_altitude_km": target_perigee_altitude / 1000.0,
            "target_apogee_altitude_km": target_apogee_altitude / 1000.0,
            "target_semi_major_axis": 0.5 * (rp_target + ra_target),
            "target_eccentricity": target_e,
            "target_inclination": current["inclination"],
            "target_raan": current["raan"],
            "target_argument_of_periapsis": current["argument_of_periapsis"],
            "delta_v": abs(best["delta_v1"]) + abs(best["delta_v2"]),
            "total_delta_v": abs(best["delta_v1"]) + abs(best["delta_v2"]),
            "total_propellant": best["propellant_burn1"] + best["propellant_burn2"],
            "target_radius": best["endpoint_radius"],
        }

    def calculate_hohmann_transfer(self, target_altitude_km):
        return self.calculate_apsidal_transfer(target_altitude_km, target_altitude_km)

    def execute_transfer(
        self, target_perigee_altitude_km, target_apogee_altitude_km=None,
        target_inclination_deg=None
    ):
        if target_apogee_altitude_km is None:
            target_apogee_altitude_km = target_perigee_altitude_km
        plan = self.calculate_apsidal_transfer(
            target_perigee_altitude_km, target_apogee_altitude_km
        )
        if target_inclination_deg is not None:
            target_inclination_deg = float(target_inclination_deg)
            if not math.isfinite(target_inclination_deg) or not 0 <= target_inclination_deg <= 180:
                raise ValueError("Target inclination must be between 0 and 180 degrees.")
            if not math.isclose(
                target_inclination_deg,
                plan["initial_inclination_deg"],
                abs_tol=1e-6,
            ):
                raise ValueError(
                    "Apsidal transfers are coplanar. Execute the inclination change separately first."
                )

        self.active_transfer = dict(plan)
        self.active_transfer.update({
            "first_burn_pending": True,
            "first_burn_executed": False,
            "status": f"WAITING FOR {plan['start_apsis'].upper()}",
        })
        if self._apsis_event_is_here(plan["start_apsis"]):
            self._execute_first_burn()
        else:
            self.last_maneuver = {
                "type": "APSIDAL TRANSFER SCHEDULED",
                "time": self.elapsed_time,
                "delta_v": plan["total_delta_v"],
            }
        if self.active_transfer is None:
            plan.update({
                "first_burn_pending": False,
                "first_burn_executed": True,
                "status": "COMPLETED",
            })
            return plan
        return self.active_transfer.copy()

    def _execute_first_burn(self):
        plan = self.active_transfer
        position = self.current_state[:3]
        velocity = self.current_state[3:]
        r_hat = position / np.linalg.norm(position)
        radial = float(np.dot(velocity, r_hat))
        tangent_vector = velocity - radial * r_hat
        tangent_speed = float(np.linalg.norm(tangent_vector))
        if tangent_speed <= 1e-12:
            raise RuntimeError("Invalid transverse velocity at the first apsidal burn.")
        tangent = tangent_vector / tangent_speed
        if plan["single_burn"]:
            target_speed = math.sqrt(MU_EARTH / np.linalg.norm(position))
        else:
            target_speed = math.sqrt(
                MU_EARTH * (
                    2.0 / np.linalg.norm(position)
                    - 1.0 / plan["transfer_semi_major_axis"]
                )
            )
        dv = target_speed - tangent_speed
        fuel = self._propellant_for_dv(dv)
        self.spacecraft.consume_propellant(fuel)
        self.current_state[3:] = velocity + dv * tangent
        self.spacecraft.set_states(self.current_state)
        self.history.append(self.current_state.copy())
        self.state_version += 1

        plan["first_burn_pending"] = False
        plan["first_burn_executed"] = True
        plan["delta_v1_actual"] = dv
        plan["propellant_burn1_actual"] = fuel
        plan["burn1_time"] = self.elapsed_time
        plan["burn2_time"] = (
            self.elapsed_time + plan["transfer_time"]
            if not plan["single_burn"]
            else self.elapsed_time
        )
        if plan["single_burn"]:
            self.active_transfer = None
            self.last_maneuver = {
                "type": "CIRCULARIZATION COMPLETED",
                "time": self.elapsed_time,
                "delta_v": abs(dv),
                "target_perigee_altitude_km": plan["target_perigee_altitude_km"],
                "target_apogee_altitude_km": plan["target_apogee_altitude_km"],
            }
        else:
            plan["status"] = f"TRANSFER TO {plan['endpoint_apsis'].upper()}"
            plan["second_burn_apsis"] = (
                "apogee" if plan["endpoint_radius"] > plan["start_radius"]
                else "perigee"
            )
            self.last_maneuver = {
                "type": "APSIDAL TRANSFER FIRST BURN",
                "time": self.elapsed_time,
                "delta_v": abs(dv),
            }

    def _execute_second_burn(self):
        plan = self.active_transfer
        position = self.current_state[:3]
        velocity = self.current_state[3:]
        radius = float(np.linalg.norm(position))
        r_hat = position / radius
        radial = float(np.dot(velocity, r_hat))
        tangent_vector = velocity - radial * r_hat
        tangent_speed = float(np.linalg.norm(tangent_vector))
        if tangent_speed <= 1e-12:
            raise RuntimeError("Invalid transverse velocity at the second apsidal burn.")
        tangent = tangent_vector / tangent_speed
        target_speed = math.sqrt(
            MU_EARTH * (2.0 / radius - 1.0 / plan["target_semi_major_axis"])
        )
        dv = target_speed - tangent_speed
        fuel = self._propellant_for_dv(dv)
        self.spacecraft.consume_propellant(fuel)
        self.current_state[3:] = velocity + dv * tangent
        self.spacecraft.set_states(self.current_state)
        self.history.append(self.current_state.copy())
        self.state_version += 1
        self.active_transfer = None
        self.last_maneuver = {
            "type": "APSIDAL TRANSFER COMPLETED",
            "time": self.elapsed_time,
            "delta_v": plan["total_delta_v"],
            "burn_radius": radius,
            "target_perigee_altitude_km": plan["target_perigee_altitude_km"],
            "target_apogee_altitude_km": plan["target_apogee_altitude_km"],
            "propellant_burn1": plan["propellant_burn1_actual"],
            "propellant_burn2": fuel,
        }

    def _propagate(self, state, duration):
        if duration <= 0:
            return state.copy()
        _, states = integrate(
            state,
            duration,
            min(duration, self.integration_dt),
            self.spacecraft,
            MU_EARTH,
            self.environment,
        )
        return states[-1].copy()

    def _crosses_apsis(self, before, after, apsis_type):
        if apsis_type == "perigee":
            return before < 0.0 and after >= 0.0
        return before > 0.0 and after <= 0.0

    def _locate_apsis(self, state, duration, apsis_type):
        start_rate = self._apsis_radial_speed(state)
        low, high = 0.0, duration
        for _ in range(48):
            middle = 0.5 * (low + high)
            candidate = self._propagate(state, middle)
            rate = self._apsis_radial_speed(candidate)
            if self._crosses_apsis(start_rate, rate, apsis_type):
                high = middle
            else:
                low = middle
        event_time = 0.5 * (low + high)
        return event_time, self._propagate(state, event_time)

    def advance(self, duration):
        self._check()
        duration = float(duration)
        if not math.isfinite(duration) or duration < 0:
            raise ValueError("Duration must be finite and nonnegative.")
        remaining = duration

        while remaining > 1e-10:
            step = min(self.integration_dt, remaining)
            state_before = self.current_state.copy()
            next_state = self._propagate(state_before, step)

            if self.active_transfer is not None:
                apsis_type = (
                    self.active_transfer["start_apsis"]
                    if self.active_transfer["first_burn_pending"]
                    else self.active_transfer["second_burn_apsis"]
                )
                rate_before = self._apsis_radial_speed(state_before)
                rate_after = self._apsis_radial_speed(next_state)
                if self._crosses_apsis(rate_before, rate_after, apsis_type):
                    event_time, event_state = self._locate_apsis(
                        state_before, step, apsis_type
                    )
                    self.current_state = event_state
                    self.spacecraft.set_states(event_state)
                    self.elapsed_time += event_time
                    remaining -= event_time
                    self.history.append(event_state.copy())
                    if self.active_transfer["first_burn_pending"]:
                        self._execute_first_burn()
                    else:
                        self._execute_second_burn()
                    continue

            self.current_state = next_state
            self.spacecraft.set_states(next_state)
            self.elapsed_time += step
            remaining -= step
            self.history.append(next_state.copy())

        return self.current_state.copy()

    def get_telemetry(self):
        self._check()
        position = self.get_position()
        velocity = self.get_velocity()
        radius = float(np.linalg.norm(position))
        speed = float(np.linalg.norm(velocity))
        elements = self.get_orbital_elements()
        return {
            "time": self.elapsed_time,
            "position": position,
            "velocity": velocity,
            "altitude_km": (radius - EARTH_RADIUS) / 1000.0,
            "radius_km": radius / 1000.0,
            "speed_km_s": speed / 1000.0,
            "perigee_altitude_km": (
                elements["periapsis_radius"] - EARTH_RADIUS
            ) / 1000.0,
            "apogee_altitude_km": (
                elements["apoapsis_radius"] - EARTH_RADIUS
            ) / 1000.0 if elements["conic_type"] == "elliptic" else math.inf,
            "semi_major_axis_km": elements["semi_major_axis"] / 1000.0,
            "eccentricity": elements["eccentricity"],
            "inclination_deg": math.degrees(elements["inclination"]),
            "orbital_period_s": elements["orbital_period"],
            "true_anomaly_deg": math.degrees(elements["true_anomaly"]),
            "argument_of_periapsis_deg": math.degrees(
                elements["argument_of_periapsis"]
            ),
            "conic_type": elements["conic_type"],
            "mass_kg": self.spacecraft.net_mass,
            "propellant_kg": self.spacecraft.get_remaining_propellant(),
            "transfer_active": self.active_transfer is not None,
            "maneuver_status": (
                self.active_transfer["status"]
                if self.active_transfer is not None
                else self.last_maneuver["type"] if self.last_maneuver else "NOMINAL"
            ),
        }
