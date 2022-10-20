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
TUBE_COLOR_CHOICES = ["green", "red", "blue"]


class CustomSlider(QtWidgets.QSlider):
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
    def __init__(self, parent=None):
        super().__init__(parent)

        btnSize = QtCore.QSize(16, 16)

        layout = QtWidgets.QVBoxLayout()
        self.tube_color_label = QtWidgets.QLabel("Object Colours:")
        layout.addWidget(self.tube_color_label)
        self.tube_color_chooser = QtWidgets.QComboBox()
        self.tube_color_chooser.addItems(TUBE_COLOR_CHOICES)
        layout.addWidget(self.tube_color_chooser)

        layout.addStretch(1)
        # self.setLayout(layout)

        self.playButton = QtWidgets.QPushButton()
        self.playButton.setEnabled(True)
        self.playButton.setFixedHeight(24)
        self.playButton.setIconSize(btnSize)
        self.playButton.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        )

        self.positionSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.positionSlider = CustomSlider(QtCore.Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.slider_max = -1
        # self.positionSlider.sliderMoved.connect(self.setPosition)

        # self.statusBar = QtWidgets.QStatusBar()
        # self.statusBar.setFont(QtGui.QFont("Noto Sans", 7))
        # self.statusBar.setFixedHeight(14)

        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setRange(0, 0)
        self.progressBar.setFormat("Calculating Meshdata... %p%")

        controlLayout = QtWidgets.QHBoxLayout()
        controlLayout = QtWidgets.QGridLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton, 0, 0)
        controlLayout.addWidget(self.positionSlider, 0, 1)
        controlLayout.addWidget(self.progressBar, 1, 0, -1, -1)
        self.setLayout(controlLayout)

    # If playing then dont do anything, or maybe not???
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Right:
            self.positionSlider.setValue(self.slider.value() + 1)
        elif event.key() == QtCore.Qt.Key_Left:
            self.positionSlider.setValue(self.slider.value() - 1)
        else:
            QtWidgets.QWidget.keyPressEvent(self, event)


class CanvasWrapper:
    def __init__(self, visualization_dict):

        self.canvas = SceneCanvas(keys="interactive", size=CANVAS_SIZE, bgcolor="black")
        self.view = self.canvas.central_widget.add_view()
        self.visualization_dict = visualization_dict
        self.objects = {}
        self.meshdata_cache = []
        self.data_length = len(visualization_dict["time"])

        for num, object in enumerate(visualization_dict["objects"]):

            print("Launching...")
            object_parameters = visualization_dict["objects"][object]
            object_type = object_parameters["type"]

            if object_type == "rod":

                is_closed = object_parameters["closed"]
                color = object_parameters["color"]
                # color = TUBE_COLOR_CHOICES[0]

                # Object position must be transposed from the way that PyElastica
                # saves it during callback.
                # TODO: Transpose position data during generation of visualization_dict
                #  instead of here

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

        time_data = visualization_dict["time"]
        self.time_text = scene.Text(
            f"Time: {time_data[0]:.4f}",
            bold=True,
            font_size=14,
            color="w",
            pos=(80, 30),
            parent=self.canvas.central_widget,
        )

        # self.view.camera = scene.TurntableCamera(elevation=0, azimuth=0)
        # self.view.camera.set_range(
        #     x=(-0.1, 0.1),
        #     y=(0, 0),
        #     z=(0, 1),
        # )
        self._calculate_domain()

    def set_tube_color(self, color):
        print(f"Changing tube color")
        for object in self.objects:
            self.objects[object].set_data(color=color)

    def update_from_slider(self, index):
        
        for object in self.meshdata_cache[index]["objects"]:
            self.objects[object].set_data(
                meshdata=self.meshdata_cache[index]["objects"][object]
            )

        self.time_text.text = f"Time: {self.meshdata_cache[index]['time']:.4f}"

    def update_cache(self, new_meshdata_dict):

        self.meshdata_cache.append(new_meshdata_dict)

    def add_axis(
        self, axis_direction, domain=None, color="white", font_size=10, axis_width=2
    ):

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

            rot_mat = np.array(
                [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]
            )
            axis.transform = scene.transforms.MatrixTransform(matrix=rot_mat)

    def turntable_camera(self, focal_plane="xz", **kwargs):

        self.camera_type = "turntable"
        self.view.camera = scene.TurntableCamera(elevation=0, azimuth=0)
        self.view.camera.set_range(
            x=(self.min_domain[0], self.max_domain[0]),
            y=(self.min_domain[1], self.max_domain[1]),
            z=(self.min_domain[2], self.max_domain[2]),
        )

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

        self.camera_type = "arcball"
        self.view.camera = scene.ArcballCamera()
        self.view.camera.set_range(
            x=(self.min_domain[0], self.max_domain[0]),
            y=(self.min_domain[1], self.max_domain[1]),
            z=(self.min_domain[2], self.max_domain[2]),
        )
        print(self.view.camera.get_state())

    def fly_camera(self, autoroll=True, **kwargs):

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

        self.is_playing = False
        self.play_timer = QtCore.QTimer()

        self._connect_controls()
        self.setWindowTitle("PyElastica Interactive Visualization")

    def _connect_controls(self):
        self._play_pause_controls.positionSlider.valueChanged.connect(
            self._canvas_wrapper.update_from_slider
        )
        self._play_pause_controls.playButton.clicked.connect(self.playButtonPressEvent)
        self.play_timer.timeout.connect(self.increment_slider)

    def update_meshdata_progress(self, _):

        self._play_pause_controls.slider_max += 1
        self._play_pause_controls.positionSlider.setMaximum(
            self._play_pause_controls.slider_max
        )
        self._play_pause_controls.progressBar.setValue(
            self._play_pause_controls.slider_max
        )

    def increment_slider(self):

        current_val = self._play_pause_controls.positionSlider.value()

        if current_val < self._play_pause_controls.slider_max:

            self._play_pause_controls.positionSlider.setValue(current_val + 1)

            if current_val + 1 >= self._play_pause_controls.slider_max:
                self.playButtonPressEvent()

    def set_pbar_length(self, value):
        self._play_pause_controls.progressBar.setMaximum(value - 1)

    def playButtonPressEvent(self):

        if not self.is_playing:
            self._play_pause_controls.playButton.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause)
            )
            self.play_timer.start()
            self.is_playing = True

        elif self.is_playing:
            self._play_pause_controls.playButton.setIcon(
                self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
            )
            self.play_timer.stop()
            self.is_playing = False

    def closeEvent(self, event):
        print("Closing main window!")
        self.closing.emit()
        return super().closeEvent(event)


class DataSource(QtCore.QObject):
    """Object representing a complex data producer."""

    new_data = QtCore.pyqtSignal(dict)
    finished = QtCore.pyqtSignal()

    def __init__(self, visualization_dict, parent=None):
        super().__init__(parent)
        self._should_end = False
        self.visualization_dict = visualization_dict
        self._num_iters = len(self.visualization_dict["time"])

    def run_data_creation(self):
        print("Run data creation is starting")

        for i in range(self._num_iters):
            if self._should_end:
                print("Data source saw that it was told to stop")
                break

            data_dict = {"objects": {}}

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
                    )._meshdata

                    data_dict["objects"][f"{object}_{num}"] = tube_meshdata

            data_dict["time"] = self.visualization_dict["time"][i]
            self.new_data.emit(data_dict)

        print("Data source finishing")
        self.finished.emit()

    def stop_data(self):
        print("Data source is quitting...")
        self._should_end = True


if __name__ == "__main__":

    with open("examples/ContinuumSnakeCase/continuum_snake.dat", "rb") as f:
        postprocessing_dict = pickle.load(f)

    visualization_dict = generate_visualization_dict(postprocessing_dict)

    app = use_app("pyqt5")
    app.create()

    canvas_wrapper = CanvasWrapper(visualization_dict)
    canvas_wrapper.add_axis("z")
    canvas_wrapper.add_axis("x")
    canvas_wrapper.turntable_camera()
    # canvas_wrapper.add_time()
    win = GUIMainWindow(canvas_wrapper)
    win.set_pbar_length(canvas_wrapper.data_length)

    data_thread = QtCore.QThread(parent=win)
    data_source = DataSource(visualization_dict)
    data_source.moveToThread(data_thread)

    # update the visualization when there is new data
    ##### data_source.new_data.connect(canvas_wrapper.update_data)

    data_source.new_data.connect(canvas_wrapper.update_cache)
    data_source.new_data.connect(win.update_meshdata_progress)
    # start data generation when the thread is started
    data_thread.started.connect(data_source.run_data_creation)
    # if the data source finishes before the window is closed, kill the thread
    data_source.finished.connect(data_thread.quit, QtCore.Qt.DirectConnection)
    # if the window is closed, tell the data source to stop
    win.closing.connect(data_source.stop_data, QtCore.Qt.DirectConnection)
    # when the thread has ended, delete the data source from memory
    data_thread.finished.connect(data_source.deleteLater)

    win.show()
    data_thread.start()
    app.run()

    print("Waiting for data source to close gracefully...")
    data_thread.wait(5000)
