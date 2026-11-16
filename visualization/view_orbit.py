import vispy
vispy.use("pyside6")
from vispy import scene
from visualization.earth_renderer import create_earth
from visualization.trajectory_renderer import create_trajectory
from visualization.spacecraft_renderer import create_spacecraft_marker

class OrbitViewer:
    def __init__(self, trajectory):
        self.canvas = scene.SceneCanvas(keys="interactive", show=True, bgcolor="#07111f")
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.TurntableCamera(fov=45, distance=18000000)
        create_earth(self.view.scene)
        create_trajectory(trajectory.get_positions(), self.view.scene)
        if len(trajectory.states):
            create_spacecraft_marker(trajectory.states[-1, :3], self.view.scene)
    def show(self):
        self.canvas.show()
