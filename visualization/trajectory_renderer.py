from vispy import scene

def create_trajectory(points, parent, color=(1, 0.2, 0.2, 1), width=2):
    return scene.visuals.Line(pos=points, color=color, width=width, parent=parent)

def update_trajectory(line, points, color=(1, 0.2, 0.2, 1), width=2):
    line.set_data(pos=points, color=color, width=width)
