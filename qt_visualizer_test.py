import pickle
import time

import numpy as np
from PyQt5 import QtWidgets, QtCore

from vispy import app, scene
from vispy.scene import SceneCanvas, visuals, Text
from vispy.app import use_app

from utils import generate_visualization_dict

IMAGE_SHAPE = (600, 800)  # (height, width)
CANVAS_SIZE = (800, 600)  # (width, height)
NUM_LINE_POINTS = 200

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

        self.canvas = SceneCanvas(keys="interactive", size=CANVAS_SIZE, bgcolor="black")
        self.view = self.canvas.central_widget.add_view()
        self.objects = {}
        
        for num, object in enumerate(visualization_dict["objects"]):
            
            print("Here we go!!!")
            object_parameters = visualization_dict["objects"][object]
            object_type = object_parameters["type"]

            if object_type == "rod":

                is_closed = object_parameters["closed"]
                # color = object_parameters["color"]
                color = TUBE_COLOR_CHOICES[0]

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

                self.objects[f"{object}_{num}"] = visuals.Tube(points=[[0, 0, 0], [1, 1, 1]], color=color, parent=self.view.scene, name=f"{object}")
                self.objects[f"{object}_{num}"].set_data(meshdata=initial_tube_meshdata)
                
                # self.view.add(self.objects[f"{object}_{num}"])

            elif object_type == "sphere":

                raise NotImplementedError(
                    "TODO: Implement other shapes and object visualization"
                )
            else:

                raise ValueError("Not valid object type")
        
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

        # image_data = _generate_random_image_data(IMAGE_SHAPE)
        # self.image = visuals.Image(
        #     image_data,
        #     texture_format="auto",
        #     cmap=COLORMAP_CHOICES[0],
        #     parent=self.view_top.scene,
        # )
        # self.view_top.camera = "panzoom"
        # self.view_top.camera.set_range(x=(0, IMAGE_SHAPE[1]), y=(0, IMAGE_SHAPE[0]), margin=0)

        # self.view_bot = self.grid.add_view(1, 0, bgcolor='#c0c0c0')
        # line_data = _generate_random_line_positions(NUM_LINE_POINTS)
        # self.line = visuals.Line(line_data, parent=self.view_bot.scene, color=LINE_COLOR_CHOICES[0])
        # self.view_bot.camera = "panzoom"
        # self.view_bot.camera.set_range(x=(0, NUM_LINE_POINTS), y=(0, 1))

    def set_tube_color(self, color):
        print(f"Changing tube color")
        for object in self.objects:
            self.objects[object].set_data(color=color)       

    # def set_image_colormap(self, cmap_name: str):
    #     print(f"Changing image colormap to {cmap_name}")
    #     self.image.cmap = cmap_name

    # def set_line_color(self, color):
    #     print(f"Changing line color to {color}")
    #     self.line.set_data(color=color)

    def update_data(self, new_meshdata_dict):
        print("Updating data...")
        for object in new_meshdata_dict:
            self.objects[object].set_data(meshdata=new_meshdata_dict[object])

    def add_time(self):

        time_data = visualization_dict["time"]
        self.time_text = Text(
            f"Time: {time_data[234]:.4f}",
            bold=True,
            font_size=14,
            color="w",
            pos=(80, 30),
            parent=self.canvas.central_widget,
        )

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
    # def update_data(self, new_data_dict):
    #     print("Updating data...")
    #     self.image.set_data(new_data_dict["image"])
    #     self.line.set_data(new_data_dict["line"])


# def _generate_random_image_data(shape, dtype=np.float32):
#     rng = np.random.default_rng()
#     data = rng.random(shape, dtype=dtype)
#     return data


# def _generate_random_line_positions(num_points, dtype=np.float32):
#     rng = np.random.default_rng()
#     pos = np.empty((num_points, 2), dtype=np.float32)
#     pos[:, 0] = np.arange(num_points)
#     pos[:, 1] = rng.random((num_points,), dtype=dtype)
#     return pos


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
        self._controls.tube_color_chooser.currentTextChanged.connect(self._canvas_wrapper.set_tube_color)

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
        self._num_iters = len(visualization_dict["time"])
        self.visualization_dict = visualization_dict    

    def run_data_creation(self):
        print("Run data creation is starting")
        print("having a little nap")
        time.sleep(5)
        for i in range(self._num_iters):
            if self._should_end:
                print("Data source saw that it was told to stop")
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

                    data_dict[f"{object}_{num}"] = tube_meshdata    
            
            # time.sleep(1.0)
            self.new_data.emit(data_dict)
        
        print("Data source finishing")
        self.finished.emit()

    # def _update_image_data(self, count):
    #     img_count = count % IMAGE_SHAPE[1]
    #     self._image_data[:, img_count] = img_count / IMAGE_SHAPE[1]
    #     rdata_shape = (IMAGE_SHAPE[0], IMAGE_SHAPE[1] - img_count - 1)
    #     self._image_data[:, img_count + 1:] = _generate_random_image_data(rdata_shape)
    #     return self._image_data.copy()

    # def _update_line_data(self, count):
    #     self._line_data[:, 1] = np.roll(self._line_data[:, 1], -1)
    #     self._line_data[-1, 1] = abs(sin((count / self._num_iters) * 16 * pi))
    #     return self._line_data

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
    canvas_wrapper.add_axis("z", domain=[0, 1])
    canvas_wrapper.add_axis("x", domain=[-0.2, 0.2])
    # canvas_wrapper.add_time()
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

    print("Waiting for data source to close gracefully...")
    data_thread.wait(5000)