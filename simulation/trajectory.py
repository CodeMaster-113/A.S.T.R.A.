import numpy as np

class Trajectory:
    def __init__(self, times=None, states=None):
        self.times = np.asarray(times if times is not None else [], dtype=float)
        self.states = np.asarray(states if states is not None else [], dtype=float)
        if len(self.states) and (self.states.ndim != 2 or self.states.shape[1] != 6):
            raise ValueError("States must have shape (N, 6).")
    def get_positions(self):
        return self.states[:, :3]
    def get_velocities(self):
        return self.states[:, 3:]
    def get_times(self):
        return self.times
    def append(self, times, states):
        times, states = np.asarray(times), np.asarray(states)
        if len(self.times):
            times, states = times[1:], states[1:]
        self.times = np.concatenate((self.times, times))
        self.states = np.concatenate((self.states, states), axis=0) if len(self.states) else states.copy()
