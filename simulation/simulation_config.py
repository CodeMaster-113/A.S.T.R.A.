from physics.constants import MU_EARTH, EARTH_RADIUS
from orbital_mechanics.orbital_geometry import orbital_period

class SimulationConfig:
    def __init__(self, dt=1.0, duration=None, integrator="rk4",
                 include_j2=True, include_drag=True,
                 initial_position=None, initial_velocity=None):
        if dt <= 0:
            raise ValueError("dt must be positive.")
        if integrator.lower() != "rk4":
            raise ValueError("Only RK4 is currently implemented.")
        self.dt = float(dt)
        self.integrator = "rk4"
        self.include_j2 = bool(include_j2)
        self.include_drag = bool(include_drag)
        self.initial_position = initial_position
        self.initial_velocity = initial_velocity
        self.duration = duration if duration is not None else orbital_period(EARTH_RADIUS+400000, MU_EARTH)
        self.environment = {"include_j2": self.include_j2, "include_drag": self.include_drag, "mu": MU_EARTH}
