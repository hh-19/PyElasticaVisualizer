import numpy as np
import time
from PyQt5 import QtWidgets, QtCore

from vispy import scene
from vispy.app import use_app

CANVAS_SIZE = (800, 600)  # (width, height)
TUBE_COLOR_CHOICES = ["green", "red", "blue"]


class Controls(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.tube_color_label = QtWidgets.QLabel("Object Colours:")
        layout.addWidget(self.tube_color_label)
        self.tube_color_chooser = QtWidgets.QComboBox()
        self.tube_color_chooser.addItems(TUBE_COLOR_CHOICES)
        layout.addWidget(self.tube_color_chooser)

        layout.addStretch(1)
        self.setLayout(layout)


class CanvasWrapper:
    def __init__(self, visualization_dict):

        self.canvas = scene.SceneCanvas(keys="interactive", size=CANVAS_SIZE, bgcolor="black")
        self.view = self.canvas.central_widget.add_view()
        self.objects = {}

        for _, object in enumerate(visualization_dict["objects"]):

            object_parameters = visualization_dict["objects"][object]
            object_type = object_parameters["type"]

            if object_type == "rod":

                is_closed = object_parameters["closed"]
                color = TUBE_COLOR_CHOICES[0]

                object_position = object_parameters["position"][0].transpose()[:-1]
                object_radius = object_parameters["radius"][0]

                # Calculates tube meshdata
                initial_tube_meshdata = scene.visuals.Tube(
                    points=object_position,
                    radius=object_radius,
                    closed=is_closed,
                    color=color,
                )._meshdata

                self.objects[f"{object}"] = scene.visuals.Tube(
                    points=[[0, 0, 0], [1, 1, 1]],
                    parent=self.view.scene,
                    name=f"{object}",
                )
                self.objects[f"{object}"].set_data(meshdata=initial_tube_meshdata)

        time_data = visualization_dict["time"]
        self.time_text = scene.Text(
            f"Time: {time_data[234]:.4f}",
            bold=True,
            font_size=14,
            color="w",
            pos=(80, 30),
            parent=self.canvas.central_widget,
        )

        self.view.camera = scene.TurntableCamera(elevation=0, azimuth=0)
        self.view.camera.set_range(
            x=(-0.1, 0.1),
            y=(0, 0),
            z=(0, 1),
        )


    def set_tube_color(self, color):
        # In this minimal code example set_tube_colour 
        # wont work as it gets overwritten by meshdata
        print(f"Changing tube color")
        for object in self.objects:
            self.objects[object].set_data(color=color)

    def update_data(self, new_data_dict):
        for object in self.objects:
            self.objects[object].set_data(meshdata=new_data_dict[object])
        self.time_text.text = f"Time: {new_data_dict['time']:.4f}"

    def add_axis(
        self, axis_direction, domain=None, color="white", font_size=10, axis_width=2
    ):
        # ... 
        min_val, max_val = domain[0], domain[1]

        if min_val == max_val:
            return

        if axis_direction == "x":

            axis = scene.Axis(
                pos=[[min_val, 0], [max_val, 0]],
                domain=domain,
                tick_direction=(0, -1),
                parent=self.view.scene,
            )

        elif axis_direction == "z":

            axis = scene.Axis(
                pos=[[0, min_val], [0, max_val]],
                domain=domain,
                tick_direction=(-1, 0),
                parent=self.view.scene,
            )

            rot_mat = np.array(
                [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]
            )
            axis.transform = scene.transforms.MatrixTransform(matrix=rot_mat)
        # ...

class MyMainWindow(QtWidgets.QMainWindow):
    closing = QtCore.pyqtSignal()

    def __init__(self, canvas_wrapper: CanvasWrapper, *args, **kwargs):
        super().__init__(*args, **kwargs)

        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout()

        self._controls = Controls()
        main_layout.addWidget(self._controls)
        self._canvas_wrapper = canvas_wrapper
        main_layout.addWidget(self._canvas_wrapper.canvas.native)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self._connect_controls()

    def _connect_controls(self):
        self._controls.tube_color_chooser.currentTextChanged.connect(
            self._canvas_wrapper.set_tube_color
        )

    def closeEvent(self, event):
        print("Closing main window!")
        self.closing.emit()
        return super().closeEvent(event)


class DataSource(QtCore.QObject):

    new_data = QtCore.pyqtSignal(dict)
    finished = QtCore.pyqtSignal()

    def __init__(self, visualization_dict, parent=None):
        super().__init__(parent)
        self._should_end = False
        self._num_iters = len(visualization_dict["time"])
        self.visualization_dict = visualization_dict

    def run_data_creation(self):
        print("Run data creation is starting")
        for i in range(self._num_iters):
            if self._should_end:
                break

            data_dict = {}

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

                    data_dict[f"{object}"] = tube_meshdata

            data_dict["time"] = visualization_dict["time"][i]    
            self.new_data.emit(data_dict)

        self.finished.emit()

    def stop_data(self):
        self._should_end = True


if __name__ == "__main__":

    time_arr = np.linspace(0, 10, 1000)
    object_x = np.array(
        [0.1 * np.sin(np.linspace(0, 2 * np.pi, 80) + 16 * t / np.pi) for t in time_arr]
    )
    object_z = np.array(
        [np.linspace(0, 0.3, 80) + z_shift for z_shift in np.linspace(0, 0.95, 1000)]
    )
    object_y = np.zeros(shape=(1000, 80))

    object_coords = np.stack(arrays=[object_x, object_y, object_z], axis=1)
    object_radius = np.full((1000, 79), 0.00385)

    visualization_dict = {
        "objects": {
            "shearable_rod": {
                "type": "rod",
                "position": object_coords,
                "radius": object_radius,
                "color": "purple",
                "closed": False,
            }
        },
        "time": time_arr
    }

    app = use_app("pyqt5")
    app.create()

    canvas_wrapper = CanvasWrapper(visualization_dict)
    canvas_wrapper.add_axis("z", domain=[0, 1])
    canvas_wrapper.add_axis("x", domain=[-0.2, 0.2])

    win = MyMainWindow(canvas_wrapper)
    data_thread = QtCore.QThread(parent=win)
    data_source = DataSource(visualization_dict)
    data_source.moveToThread(data_thread)

    # update the visualization when there is new data
    data_source.new_data.connect(canvas_wrapper.update_data)
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

    data_thread.wait(5000)