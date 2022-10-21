import pickle
import time

import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui

from vispy import app, scene
from vispy.scene import SceneCanvas, visuals, Text
from vispy.app import use_app

from utils import generate_visualization_dict

IMAGE_SHAPE = (600, 800)  # (height, width)
CANVAS_SIZE = (800, 600)  # (width, height)


class CustomSlider(QtWidgets.QSlider):
    """Custom slider class based off QSlider to change slider position on mouse click"""

    def mousePressEvent(self, event):
        super(CustomSlider, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            val = self.pixelPosToRangeValue(event.pos())
            self.setValue(val)

    def pixelPosToRangeValue(self, pos):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(
            QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderGroove, self
        )
        sr = self.style().subControlRect(
            QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self
        )

        if self.orientation() == QtCore.Qt.Horizontal:
            sliderLength = sr.width()
            sliderMin = gr.x()
            sliderMax = gr.right() - sliderLength + 1
        else:
            sliderLength = sr.height()
            sliderMin = gr.y()
            sliderMax = gr.bottom() - sliderLength + 1
        pr = pos - sr.center() + sr.topLeft()
        p = pr.x() if self.orientation() == QtCore.Qt.Horizontal else pr.y()
        return QtWidgets.QStyle.sliderValueFromPosition(
            self.minimum(),
            self.maximum(),
            p - sliderMin,
            sliderMax - sliderMin,
            opt.upsideDown,
        )


class PlayPauseControls(QtWidgets.QWidget):
    """Group of QT widgets that control the playback of the visualizer

    Groups together the play/pause button widget, slider widget and the progress bar widget
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        btnSize = QtCore.QSize(16, 16)

        # Sets up the play button widget
        self.play_button = QtWidgets.QPushButton()
        self.play_button.setEnabled(True)
        self.play_button.setFixedHeight(24)
        self.play_button.setIconSize(btnSize)
        self.play_button.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        )

        # Sets up the position slider widget from the custom slider class
        self.position_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.position_slider = CustomSlider(QtCore.Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.slider_max = -1

        # Sets up the progress bar widget
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("Calculating Meshdata... %p%")

        # Widgets are placed within QGrid
        controlLayout = QtWidgets.QHBoxLayout()
        controlLayout = QtWidgets.QGridLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.play_button, 0, 0)
        controlLayout.addWidget(self.position_slider, 0, 1)
        controlLayout.addWidget(self.progress_bar, 1, 0, -1, -1)
        self.setLayout(controlLayout)

    # Increments slider on arrow key press while slider is in focus
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Right:
            self.position_slider.setValue(self.slider.value() + 1)
        elif event.key() == QtCore.Qt.Key_Left:
            self.position_slider.setValue(self.slider.value() - 1)
        else:
            QtWidgets.QWidget.keyPressEvent(self, event)


class CanvasWrapper:
    """Class that contains Vispy canvas and corresponding methods to be embedded in GUI"""

    def __init__(self, visualization_dict):

        self.canvas = SceneCanvas(keys="interactive", size=CANVAS_SIZE, bgcolor="black")
        self.view = self.canvas.central_widget.add_view()
        self.visualization_dict = visualization_dict
        self.objects = {}
        self.meshdata_cache = []
        self.data_length = len(visualization_dict["time"])

        # Iterates through objects passed in visualization dictionary
        # and intializes them into the scene

        for num, object in enumerate(visualization_dict["objects"]):

            object_parameters = visualization_dict["objects"][object]
            object_type = object_parameters["type"]

            if object_type == "rod":

                is_closed = object_parameters["closed"]
                color = object_parameters["color"]

                # Takes object position data up to -1th element so dimension matches radius dimension
                # This is due to how PyElastica functions, where position array has one more element
                # than the radius array
                object_position = object_parameters["position"][0].transpose()[:-1]
                object_radius = object_parameters["radius"][0]

                # Calculates tube meshdata
                initial_tube_meshdata = visuals.Tube(
                    points=object_position,
                    radius=object_radius,
                    closed=is_closed,
                    color=color,
                )._meshdata

                self.objects[f"{object}_{num}"] = visuals.Tube(
                    points=[[0, 0, 0], [1, 1, 1]],
                    color=color,
                    parent=self.view.scene,
                    name=f"{object}",
                )
                self.objects[f"{object}_{num}"].set_data(meshdata=initial_tube_meshdata)

            elif object_type == "sphere":

                raise NotImplementedError(
                    "TODO: Implement other shapes and object visualization"
                )
            else:

                raise ValueError("Not valid object type")

        # Add text to the scene displaying the simulation time
        time_data = visualization_dict["time"]
        self.time_text = scene.Text(
            f"Time: {time_data[0]:.4f}",
            bold=True,
            font_size=14,
            color="w",
            pos=(80, 30),
            parent=self.canvas.central_widget,
        )

        # Calculates the spatial domain traversed by the objects during the simulation
        # Used for automatic scaling of axes and camera framing
        self._calculate_domain()

    def set_tube_color(self, color):
        print(f"Changing tube color")
        for object in self.objects:
            self.objects[object].set_data(color=color)

    def _update_from_slider(self, index):
        """Updates scene to visualize the simulation at the time given by the slider value

        Args:
            index (int): Index of meshdata cache corresponding to the specified time
        """

        for object in self.meshdata_cache[index]["objects"]:
            self.objects[object].set_data(
                meshdata=self.meshdata_cache[index]["objects"][object]
            )

        self.time_text.text = f"Time: {self.meshdata_cache[index]['time']:.4f}"

    def _update_cache(self, new_meshdata_dict):
        """Adds new meshdata calculated in the background thread to cache to be used for visualization

        Args:
            new_meshdata_dict (dict): The new meshdata calcualted and emitted by the background thread
        """

        self.meshdata_cache.append(new_meshdata_dict)

    def add_axis(
        self, axis_direction, domain=None, color="white", font_size=10, axis_width=2
    ):
        """Adds an axis to the scene.

        Args:
            axis_direction (str): Can be either "x", "y" or "z".
            domain ([float, float], optional): Domain of the axis ie. the starting and ending values of the axis.
            If None, the domain is automaticaly set to the full range traversed during the simulation.
            Defaults to None.
            color (str, optional): Axis line color. Defaults to "white".
            font_size (int, optional): Axis tick font size. Defaults to 10.
            axis_width (int, optional): Axis line width size. Defaults to 2.
        """

        # If domain argument is None, use the minimum and maximum domain values calulcated
        # by self._calculate_domain()

        if domain is None:
            if axis_direction == "x":
                min_val, max_val = self.min_domain[0], self.max_domain[0]

            elif axis_direction == "y":
                min_val, max_val = self.min_domain[1], self.max_domain[1]

            elif axis_direction == "z":
                min_val, max_val = self.min_domain[2], self.max_domain[2]

            domain = [min_val, max_val]

        else:
            min_val, max_val = domain[0], domain[1]

        if min_val == max_val:
            return

        if axis_direction == "x":

            axis = scene.Axis(
                pos=[[min_val, 0], [max_val, 0]],
                domain=domain,
                tick_direction=(0, -1),
                font_size=font_size,
                axis_width=axis_width,
                axis_color=color,
                tick_color=color,
                text_color=color,
                parent=self.view.scene,
            )

        elif axis_direction == "y":

            axis = scene.Axis(
                pos=[[0, min_val], [0, max_val]],
                domain=domain,
                tick_direction=(-1, 0),
                font_size=font_size,
                axis_width=axis_width,
                axis_color=color,
                tick_color=color,
                text_color=color,
                parent=self.view.scene,
            )

        elif axis_direction == "z":

            axis = scene.Axis(
                pos=[[0, min_val], [0, max_val]],
                domain=domain,
                tick_direction=(-1, 0),
                font_size=font_size,
                axis_width=axis_width,
                axis_color=color,
                tick_color=color,
                text_color=color,
                parent=self.view.scene,
            )

            # Axis are specifed using 2D coordinates in Vispy, so requires rotation
            # to display z-axis

            # 4x4 transformation matrix that represents a rotation of y-axis to z-axis
            transform_mat = np.array(
                [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]
            )
            axis.transform = scene.transforms.MatrixTransform(matrix=transform_mat)

    def turntable_camera(self, focal_plane="xz", **kwargs):
        """3D camera class that orbits around a center point while
        maintaining a view on a center point.

        Notes
        -----
        Interaction:
            * LMB: orbits the view around its center point.
            * RMB or scroll: change scale_factor (i.e. zoom level)
            * SHIFT + LMB: translate the center point
            * SHIFT + RMB: change FOV

        Args:
            focal_plane (str, optional): The starting plane of focus of the camera. Values are "xy", "xz" and "yz".
        Defaults to "xz".
        """

        self.camera_type = "turntable"
        self.view.camera = scene.TurntableCamera(elevation=0, azimuth=0)
        self.view.camera.set_range(
            x=(self.min_domain[0], self.max_domain[0]),
            y=(self.min_domain[1], self.max_domain[1]),
            z=(self.min_domain[2], self.max_domain[2]),
        )

        # TODO: Change kwargs to state dicitonary so it is clearer what it is

        # kwargs here represents arguments that can be passed to Vispy cameras to control
        # the inital state of the camera. For example, the camera can be maunally positoned
        # by the user during visualization and then that camera state saved to be passed
        # to a subsequent visualizations of the simulation, so camera will not have to be repositioned again

        if kwargs:
            self.view.camera.set_state(**kwargs)

        elif focal_plane == "xz":
            self.view.camera.set_state({"elevation": 0, "azimuth": 0})

        elif focal_plane == "xy":
            self.view.camera.set_state({"elevation": 90, "azimuth": 0})

        elif focal_plane == "yz":
            self.view.camera.set_state({"elevation": 0, "azimuth": 90})

        else:
            raise ValueError(
                f"Focal plane = {focal_plane} is not a valid option. Please choose either 'xz', 'xy' or 'yz'"
            )

    def arcball_camera(self, **kwargs):
        """3D camera class that orbits around a center point while
        maintaining a view on a center point. Rotation of camera is "arcball" like.

        Notes
        -----
        Interaction:
            * LMB: orbits the view around its center point.
            * RMB or scroll: change scale_factor (i.e. zoom level)
            * SHIFT + LMB: translate the center point
            * SHIFT + RMB: change FOV
        """

        self.camera_type = "arcball"
        self.view.camera = scene.ArcballCamera()
        self.view.camera.set_range(
            x=(self.min_domain[0], self.max_domain[0]),
            y=(self.min_domain[1], self.max_domain[1]),
            z=(self.min_domain[2], self.max_domain[2]),
        )
        print(self.view.camera.get_state())

    def fly_camera(self, autoroll=True, **kwargs):
        """The fly camera provides a way to explore 3D data using an
        interaction style that resembles a flight simulator.

        Args:
            autoroll (bool, optional): Whether the camera auto rolls to maintain up as the z direction.
            Defaults to True.

        Notes
        -----

        Moving:
            * arrow keys, or WASD to move forward, backward, left and right
            * F and C keys move up and down
            * Space bar to brake

        Viewing:
            * Use the mouse while holding down LMB to control the pitch and yaw.
            * Alternatively, the pitch and yaw can be changed using the keys
                IKJL
            * The camera auto-rotates to make the bottom point down, manual
                rolling can be performed using Q and E.

        """

        self.camera_type = "fly"
        self.view.camera = scene.FlyCamera()
        self.view.camera.auto_roll = autoroll
        self.view.camera.set_range(
            x=(self.min_domain[0], self.max_domain[0]),
            z=(self.min_domain[2], self.max_domain[2]),
        )

        # TODO Set camera initial rotation and position so objects are framed in view

        # from vispy.util.quaternion import Quaternion

        # camera_x = (self.max_domain[0] + self.min_domain[0]) / 2
        # camera_z = (self.max_domain[2] + self.min_domain[2]) / 2
        # camera_y = -np.abs(2 * max([camera_z, camera_x]))

        # object_y = (self.max_domain[1] - self.min_domain[1]) / 2

        # self.view.camera.center = [camera_x, camera_y, camera_z]
        # camera_vector = np.array([0, object_y, 0])
        # self.view.camera.rotation1 = Quaternion(w=1, x=-1, y=0, z=0)

    def _calculate_domain(self):
        """Function to calculate the full domain traveresed by objects during the entire simulation"""

        num_objects = len(self.visualization_dict["objects"])
        all_objects_max_domain = np.zeros(shape=(num_objects, 3))
        all_objects_min_domain = np.zeros(shape=(num_objects, 3))
        all_objects_avg_coords = np.zeros(shape=(num_objects, 3))

        for num, object in enumerate(self.visualization_dict["objects"]):

            object_parameters = self.visualization_dict["objects"][object]
            object_position = object_parameters["position"]

            object_max_domain = object_position.max(axis=0).max(axis=1)
            object_min_domain = object_position.min(axis=0).min(axis=1)
            object_avg_coords = np.mean(object_position, axis=(0, 2))

            all_objects_max_domain[num] = object_max_domain
            all_objects_min_domain[num] = object_min_domain
            all_objects_avg_coords[num] = object_avg_coords

        self.average_position = np.mean(all_objects_avg_coords, axis=0).round(
            decimals=1
        )
        self.max_domain = all_objects_max_domain.max(axis=0).round(decimals=1)
        self.min_domain = all_objects_min_domain.min(axis=0).round(decimals=1)


class GUIMainWindow(QtWidgets.QMainWindow):
    """Main window class for the QT GUI

    Args:
        canvas_wrapper (CanvasWrapper): The Vispy canvas to be embedded.

    """

    closing = QtCore.pyqtSignal()

    def __init__(self, canvas_wrapper: CanvasWrapper, *args, **kwargs):
        super().__init__(*args, **kwargs)

        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()

        self._canvas_wrapper = canvas_wrapper
        main_layout.addWidget(self._canvas_wrapper.canvas.native)
        self._play_pause_controls = PlayPauseControls()
        main_layout.addWidget(self._play_pause_controls)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Timer signals the canvas to update the scene to the next frame while visualization is playing
        self.is_playing = False
        self.play_timer = QtCore.QTimer()

        self._connect_controls()
        self.setWindowTitle("PyElastica Interactive Visualization")

    def _connect_controls(self):
        """Connects the control signals to their corresponding slots"""

        # Trigers canvas update function when slider value changes
        self._play_pause_controls.position_slider.valueChanged.connect(
            self._canvas_wrapper._update_from_slider
        )
        self._play_pause_controls.play_button.clicked.connect(self.playButtonPressEvent)
        self.play_timer.timeout.connect(self.increment_slider)

    def _update_meshdata_progress(self, _):
        """Updates the progress bar to reflect the progress of meshdata caluclation and extends
        the range of the slider to allow newly calculated frames to be selected.
        """

        # Extends slider when new meshdata has been calculated
        self._play_pause_controls.slider_max += 1
        self._play_pause_controls.position_slider.setMaximum(
            self._play_pause_controls.slider_max
        )
        self._play_pause_controls.progress_bar.setValue(
            self._play_pause_controls.slider_max
        )

    def increment_slider(self):
        """Increments the slider while visualizer is playing, triggering an update of the canvas scene"""

        current_val = self._play_pause_controls.position_slider.value()

        # Visualization is paused once the end of the simulation is reached
        if current_val < self._play_pause_controls.slider_max:

            self._play_pause_controls.position_slider.setValue(current_val + 1)

            if current_val + 1 >= self._play_pause_controls.slider_max:
                self.playButtonPressEvent()

    def set_pbar_length(self, value):
        """Sets the length of the progress bar"""
        self._play_pause_controls.progress_bar.setMaximum(value - 1)

    def playButtonPressEvent(self):
        """Event logic for when play/pause button is pressed"""

        if not self.is_playing:
            self._play_pause_controls.play_button.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
            )
            self.play_timer.start()
            self.is_playing = True

        elif self.is_playing:
            self._play_pause_controls.play_button.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
            )
            self.play_timer.stop()
            self.is_playing = False

    def closeEvent(self, event):
        """Signals data threads to stop on closing of window"""
        self.closing.emit()
        return super().closeEvent(event)


class MeshdataSource(QtCore.QObject):
    """QT Object which calculates the meshdata for the objects in the simulation"""

    new_data = QtCore.pyqtSignal(dict)
    finished = QtCore.pyqtSignal()

    def __init__(self, visualization_dict, parent=None):
        super().__init__(parent)
        self._should_end = False
        self.visualization_dict = visualization_dict
        self._num_iters = len(self.visualization_dict["time"])

    def run_data_creation(self):

        # Iterates through each time step of the simulation
        for i in range(self._num_iters):
            if self._should_end:
                break

            data_dict = {"objects": {}}

            # Iterates through each object in simulation and calculates meshdata
            for num, object in enumerate(self.visualization_dict["objects"]):

                object_parameters = self.visualization_dict["objects"][object]
                object_type = object_parameters["type"]

                if object_type == "rod":

                    is_closed = object_parameters["closed"]
                    color = object_parameters["color"]

                    object_position = object_parameters["position"][i].transpose()[:-1]
                    object_radius = object_parameters["radius"][i]

                    tube_meshdata = scene.visuals.Tube(
                        points=object_position,
                        radius=object_radius,
                        closed=is_closed,
                        color=color,
                    )._meshdata

                    data_dict["objects"][f"{object}_{num}"] = tube_meshdata

            data_dict["time"] = self.visualization_dict["time"][i]

            # Emits calculated meshdata to be stored in meshdata cache in CanvasWrapper class
            self.new_data.emit(data_dict)

        print("Data source finishing")
        self.finished.emit()

    def stop_data(self):
        print("Data source is quitting...")
        self._should_end = True


class VisualizerGUI:
    """Visualizer class that wraps all GUI funcitonality"""

    def __init__(self, visualization_dict, canvas, app=None, win=None) -> None:

        # If no app instance has been passed create a new one
        if app is None:
            self.app = use_app("pyqt5")
            self.app.create()

        else:
            self.app = app

        # If no GUI window instance has been passed, create a new one
        if win is None:
            self.win = GUIMainWindow(canvas)
            self.win.set_pbar_length(canvas.data_length)

        else:
            self.win = win

        self.canvas = canvas
        self.visualization_dict = visualization_dict
        self._connect_data_source()

    def run(self):

        self.win.show()
        self.data_thread.start()
        self.app.run()

        print("Waiting for data source to close gracefully...")
        self.data_thread.wait(5000)

    def _connect_data_source(self):

        # Create meshdata source and move it to new thread
        self.data_thread = QtCore.QThread(parent=self.win)
        self.data_source = MeshdataSource(self.visualization_dict)
        self.data_source.moveToThread(self.data_thread)

        # update the visualization when there is new data
        self.data_source.new_data.connect(self.canvas._update_cache)
        self.data_source.new_data.connect(self.win._update_meshdata_progress)
        # start data generation when the thread is started
        self.data_thread.started.connect(self.data_source.run_data_creation)
        # if the data source finishes before the window is closed, kill the thread
        self.data_source.finished.connect(
            self.data_thread.quit, QtCore.Qt.DirectConnection
        )
        # if the window is closed, tell the data source to stop
        self.win.closing.connect(self.data_source.stop_data, QtCore.Qt.DirectConnection)
        # when the thread has ended, delete the data source from memory
        self.data_thread.finished.connect(self.data_source.deleteLater)


if __name__ == "__main__":

    with open("examples/ContinuumSnakeCase/continuum_snake.dat", "rb") as f:
        postprocessing_dict = pickle.load(f)

    visualization_dict = generate_visualization_dict(postprocessing_dict)

    canvas = CanvasWrapper(visualization_dict)
    canvas.add_axis("z")
    canvas.add_axis("x")
    canvas.turntable_camera()

    Visualizer = VisualizerGUI(visualization_dict, canvas)
    Visualizer.run()