import math
import numpy as np

class Spacecraft:
    def __init__(self, name, net_mass, dry_mass, states, max_thrust, specific_impulse,
                 drag_coefficient=0.0, reference_area=0.0,
                 radiation_coefficient=0.0, thrust_direction=(0.0, 0.0, 1.0)):
        self.name = str(name)
        self.net_mass = float(net_mass)
        self.dry_mass = float(dry_mass)
        self.max_thrust = float(max_thrust)
        self.specific_impulse = float(specific_impulse)
        self.drag_coefficient = float(drag_coefficient)
        self.reference_area = float(reference_area)
        self.radiation_coefficient = float(radiation_coefficient)
        self.thrust_direction = np.asarray(thrust_direction, dtype=float)
        self.thrust_active = False
        self.thrust_magnitude = 0.0
        values = (self.net_mass, self.dry_mass, self.max_thrust, self.specific_impulse,
                  self.drag_coefficient, self.reference_area, self.radiation_coefficient)
        if not all(math.isfinite(v) for v in values):
            raise ValueError("Spacecraft parameters must be finite.")
        if self.dry_mass <= 0 or self.net_mass < self.dry_mass:
            raise ValueError("Net mass must be at least positive dry mass.")
        if self.max_thrust < 0 or self.specific_impulse <= 0:
            raise ValueError("Invalid propulsion parameters.")
        if self.drag_coefficient < 0 or self.reference_area < 0 or self.radiation_coefficient < 0:
            raise ValueError("Spacecraft coefficients cannot be negative.")
        if self.thrust_direction.shape != (3,) or not np.all(np.isfinite(self.thrust_direction)):
            raise ValueError("Thrust direction must contain 3 finite values.")
        self.set_states(states)

    def get_states(self):
        return [self.xloc, self.yloc, self.zloc, self.vx, self.vy, self.vz]

    def set_states(self, new_states):
        states = [float(v) for v in new_states]
        if len(states) != 6 or not all(math.isfinite(v) for v in states):
            raise ValueError("State must contain 6 finite values.")
        self.xloc, self.yloc, self.zloc, self.vx, self.vy, self.vz = states

    def consume_propellant(self, amt):
        amt = float(amt)
        if not math.isfinite(amt) or amt < 0:
            raise ValueError("Propellant use must be finite and nonnegative.")
        if amt > self.get_remaining_propellant() + 1e-12:
            raise ValueError("Insufficient propellant.")
        self.net_mass -= amt

    def get_remaining_propellant(self):
        return self.net_mass - self.dry_mass
