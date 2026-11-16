import math
import numpy as np
from physics.equation_of_motion import state_derivative

def integrate(initial_state, duration, dt, spacecraft, mu, environment=None):
    state = np.asarray(initial_state, dtype=float).copy()
    duration, dt = float(duration), float(dt)
    if state.shape != (6,) or not np.all(np.isfinite(state)):
        raise ValueError("Initial state must contain 6 finite values.")
    if not math.isfinite(duration) or duration < 0:
        raise ValueError("Duration must be finite and nonnegative.")
    if not math.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive.")
    t = 0.0
    times, states = [t], [state.copy()]
    while t < duration - 1e-12:
        h = min(dt, duration - t)
        k1 = state_derivative(state, spacecraft, environment, mu)
        k2 = state_derivative(state + 0.5*h*k1, spacecraft, environment, mu)
        k3 = state_derivative(state + 0.5*h*k2, spacecraft, environment, mu)
        k4 = state_derivative(state + h*k3, spacecraft, environment, mu)
        state = state + (h/6.0)*(k1 + 2*k2 + 2*k3 + k4)
        t += h
        if math.isclose(t, duration, abs_tol=1e-12, rel_tol=0):
            t = duration
        spacecraft.set_states(state)
        times.append(t)
        states.append(state.copy())
    return np.asarray(times), np.asarray(states)
