from vispy import scene
from physics.constants import EARTH_RADIUS

def create_earth(parent):
    return scene.visuals.Sphere(radius=EARTH_RADIUS, method="latitude",
                                rows=40, cols=80, color=(0.05, 0.25, 0.75, 1),
                                parent=parent)
