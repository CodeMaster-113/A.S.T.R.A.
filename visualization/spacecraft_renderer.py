import numpy as np
from vispy import scene

def create_spacecraft_marker(position, parent):
    marker = scene.visuals.Markers(parent=parent)
    marker.set_data(pos=np.asarray([position]), face_color=(1, 0.55, 0.05, 1),
                    edge_color="white", size=14)
    return marker

def update_spacecraft_marker(marker, position):
    marker.set_data(pos=np.asarray([position]), face_color=(1, 0.55, 0.05, 1),
                    edge_color="white", size=14)
