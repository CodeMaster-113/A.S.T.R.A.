from physics.integrator import integrate
from physics.constants import MU_EARTH
from simulation.trajectory import Trajectory

class OrbitSimulator:
    def __init__(self, config, spacecraft):
        self.config = config
        self.spacecraft = spacecraft
        self.trajectory = Trajectory()
    def initialize(self, initial_state):
        self.initial_state = initial_state
        self.trajectory = Trajectory([0.0], [initial_state])
    def run(self, initial_state=None):
        state = initial_state if initial_state is not None else self.initial_state
        times, states = integrate(state, self.config.duration, self.config.dt,
                                  self.spacecraft, MU_EARTH, self.config.environment)
        self.trajectory = Trajectory(times, states)
        return self.trajectory
    def get_trajectory(self):
        return self.trajectory
