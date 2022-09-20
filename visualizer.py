from ast import Raise
from unicodedata import decimal
import numpy as np

from tqdm import tqdm
from vispy import app, scene
from vispy.gloo.util import _screenshot


class Visualizer:
    """Visualizer class for visualising PyElastica simulations

    Attributes
    ----------

    visualization_dict: dict
        Dictionary containing the data and parameters for each object
        in the simulation to be visualized. Visualization dictionary
        can be created using the help of utility functions provided.
    camera_type: str
        The camera type to be used during visualization.
        TODO: Allow more options and to be specified by user (potentially
        as a @property)
    objects: dict
        Dictionary of Vispy.scene.visual instances of the simulation objects to
        be visualized. Key is a string of the name of the object as given in the
        visualization dict, and the value is a Vispy.scene.visual instance
    meshdata: dict
        Dictionary of the meshdata for each object to be visualized. Key is the
        string of the name of the object as given in the visualization dict and
        the value is a list of meshdata
    app_timers: dict
        A dictionary of the Vispy app timers. Key is a string of the name of
        the timer and the value is a Vispy.app.Timer instance
        TODO: Create more timers and allow for timers to be created by users and
        added
    app: Vispy.app.application.Application()
        The Vispy app instance.
        TODO: Think about whether it would be better
        for user to create instance of app and then provide it to the class as
        potentially recommended by the Vispy maintainers
    canvas: Vispy.scene.SceneCanvas
        The Vispy scene instance.
        TODO: Think about whether it would be better
        for user to create instance of the scene and then provide it to the class as
        potentially recommended by the Vispy maintainers.
        TODO: Also scene instance has parameters and can be customised eg. background
        color and window size. Think about the best way to implement this.
    view: Vispy.view
        The view(s) in the canvas.
        TODO: Potential future features include addition views in addition to the
        central widget such as side graph views etc.
    time: list
        List of the the simulation times. Used to indicate the simulation time
        while the simulation is being visualized.
    time_text: Vispy.scene.text
        Vispy instance to display the time in the visualization window.
        TODO: Perhaps allow for ways for parameters of the text to be specified
        eg. Color, size etc.
        TODO: Enable timer to be turned on or off
    max_updates: int
        The maximum number of updates/number of times the app timers can
        run, to prevent IndexErrors.
        TODO: See comments further down about ways to improve the usage of this

    """

    def __init__(self, visualization_dict: dict, canvas_size=(800, 608)) -> None:

        self.visualization_dict = visualization_dict
        self.canvas_size = canvas_size
        self.camera_type = "turntable"
        self.save_video = False
        self.objects = {}
        self.meshdata = {}
        self.app_timers = {}

        self._calculate_meshdata()
        self._calculate_domain()
        self._initalize_scene()

    def _calculate_meshdata(self):
        """Pre-computes meshdata for objects in system

        Meshdata for each object is computed based on the the object parameters
        (eg. position, radius etc.) passed in the visualization dictionary and
        is added to the self.meshdata dictionary.

        Pre-computing meshdata before visualization begins saves a lot of time
        as opposed to computing during visualization.

        Raises:
            NotImplementedError: Error if object type is one which has not
            yet been implemented
            ValueError: Error if object type is not one of the possible
            types
        """

        number_of_objects = len(self.visualization_dict["objects"])

        print("Pre-calculating meshdata...")

        for num, object in enumerate(self.visualization_dict["objects"]):

            self.meshdata[object] = []
            object_parameters = self.visualization_dict["objects"][object]
            object_type = object_parameters["type"]

            if object_type == "rod":

                is_closed = object_parameters["closed"]
                color = object_parameters["color"]

                for i in tqdm(
                    range(len(object_parameters["position"])),
                    desc=f"Object {num+1}/{number_of_objects}",
                ):

                    # Object position must be transposed from the way that PyElastica
                    # saves it during callback.
                    # TODO: Transpose position data during generation of visualization_dict
                    #  instead of here

                    # Takes object position data up to -1th element so dimension matches radius dimension
                    # This is due to how PyElastica functions, where position array has one more element
                    # than the radius array
                    object_position = object_parameters["position"][i].transpose()[:-1]
                    object_radius = object_parameters["radius"][i]

                    # Calculates tube meshdata
                    tube_meshdata = scene.visuals.Tube(
                        points=object_position,
                        radius=object_radius,
                        closed=is_closed,
                        color=color,
                    )._meshdata

                    # print(f"Size of meshdata {sys.getsizeof(tube_meshdata)}")
                    # print(tube_meshdata)
                    self.meshdata[object].append(tube_meshdata)

            elif object_type == "sphere":

                raise NotImplementedError(
                    "TODO: Implement other shapes and object visualization"
                )
            else:

                raise ValueError("Not valid object type")

    def _initalize_scene(self) -> None:
        """Initializes the Vispy app and scene

        Creates the Vispy app and scene, and creates a main view from
        the canvas.

        Raises:
            NotImplementedError: Raises error if one of the objects is of
            a type that is not yet implemented
        """

        self.app = app.application.Application()
        self.canvas = scene.SceneCanvas(
            keys="interactive", size=self.canvas_size, bgcolor="black"
        )
        # Prints FPS to console for measuring performance
        self.canvas.measure_fps()

        # Set up a view box to display the image with interactive pan/zoom
        self.view = self.canvas.central_widget.add_view()

        # Iterates through the different objects in the system and adds their initial
        # state to the central view

        for object in self.visualization_dict["objects"]:

            object_type = self.visualization_dict["objects"][object]["type"]

            if object_type == "rod":

                initial_meshdata = self.meshdata[object][0]
                object_instance = scene.visuals.Tube(points=[[0, 0, 0], [1, 1, 1]])
                object_instance.set_data(meshdata=initial_meshdata)

                self.view.add(object_instance)
                self.objects[object] = object_instance

            elif object_type == "sphere":

                raise NotImplementedError(
                    "TODO: Implement other shapes and object visualization"
                )

        # Creates the time text and adds it to the scene
        self.time = self.visualization_dict["time"]
        self.time_text = scene.Text(
            f"Time: {self.time[0]:.4f}",
            bold=True,
            font_size=14,
            color="w",
            pos=(80, 30),
            parent=self.canvas.central_widget,
        )

    def add_axis(self, axis_direction, domain=None, color="white", font_size=10, axis_width=2):

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

            rot_mat = np.array([[1,0,0,0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]])
            axis.transform = scene.transforms.MatrixTransform(matrix=rot_mat)


    def _initialize_camera(self):
        """Intializes camera type for the scene

        TODO: Add more camera types
        TODO: Add ability for user to customize the different parameters for the
        camera

        Raises:
            ValueError: Raises error if camera option chosen is not a valid option
        """
        if self.camera_type == "turntable":

            self.view.camera = scene.TurntableCamera()
            self.view.camera.set_range()

        else:
            raise ValueError(
                f"{self.camera_type} is not a valid camera option. Please chose another camera."
            )

    def _initialize_timers(self, timers=None):
        """Method to intialize timers to be used in app

        Args:
            timers (list str): List of timers to be initialized. Defaults to None.
        """

        # for timer in self.timers:

        #     app_timer = app.Timer(interval=timer["interval"], connect=timer["func"], start=True, app=self.app)

        # This is the iterator index that controls incrementing the meshdata during update of the objects during
        # the update timer
        # TODO: Potentially look at seperate iterator indexes as more app timers are added or varying incrementation
        # eg. for increased playback speed iterator will need to be incremented more

        if timers is None:
            timers = []

        self.iterator_index = 0

        # Maximum number of updates allowed
        # TODO: Think about a better way to define/set this as it is quite
        # rudimentary now and purely used to prevent indexErrors

        self.max_updates = len(list(self.meshdata.values())[0]) - 1

        # TODO: Allow modification of the interval value
        self.app_timers["update_objects"] = app.Timer(
            interval="auto",
            connect=self._update_objects_timer,
            start=True,
            app=self.app,
        )

        if "save_video" in timers:

            self.app_timers["save_video"] = app.Timer(
                interval="auto",
                connect=self._save_video_timer,
                start=True,
                app=self.app,
            )

    def _update_objects_timer(self, event):
        """The app timer to update the objects between frames

        Args:
            event : Parameter required for Vispy app timers
        """

        self.iterator_index += 1 * 1

        # Stop the timer update to prevent list indexing beyond
        # the size of the list

        if self.iterator_index >= self.max_updates:
            # Once the update timer has reached its stopping point all other
            # timers will be closed as well

            for timers in self.app_timers:
                self.app_timers[timers].stop()

            if self.save_video == True:
                self.video_writer.close()

            self.canvas.close()
            return

        for object in self.objects:

            object_parameters = self.visualization_dict["objects"][object]
            object_type = object_parameters["type"]

            if object_type == "rod":

                # Updates the object in the scene with the next meshdata
                new_meshdata = self.meshdata[object][self.iterator_index]
                self.objects[object].set_data(meshdata=new_meshdata)

        # time_list = self.visualization_dict["time"]
        self.time_text.text = f"Time: {self.time[self.iterator_index]:.4f}"

    def _save_video_timer(self, event):
        """App timer to write simulation frames to video file"""

        frame = _screenshot()
        self.video_writer.append_data(frame)

    def _calculate_domain(self):
        
        num_objects = len(self.visualization_dict["objects"])
        all_objects_max_domain = np.zeros(shape=(num_objects, 3))
        all_objects_min_domain = np.zeros(shape=(num_objects, 3))

        for num, object in enumerate(self.visualization_dict["objects"]):

            object_parameters = self.visualization_dict["objects"][object]
            object_position = object_parameters["position"]

            object_max_domain = object_position.max(axis=0).max(axis=1)
            object_min_domain = object_position.min(axis=0).min(axis=1)

            all_objects_max_domain[num] = object_max_domain
            all_objects_min_domain[num] = object_min_domain

        self.max_domain = all_objects_max_domain.max(axis=0).round(decimals=1)
        self.min_domain = all_objects_min_domain.min(axis=0).round(decimals=1)


    def run(self, video_fname=None):
        """Runs the visualization

        Runs the different initialisation/set up methods before showing the
        Vispy canvas and starting the Vispy app and its' timers

        Args:
            video_fname (str, optional): The file path to save the video
            output of the simulation. If None, then no video is saved.
            Defaults to None.
        """

        # self._calculate_meshdata()
        # self._initalize_scene()
        self._initialize_camera()

        if video_fname is not None:

            from imageio import get_writer

            self.save_video = True
            self.video_writer = get_writer(video_fname, fps=60, quality=10)
            self._initialize_timers(timers=["save_video"])

        else:
            self._initialize_timers()

        self.canvas.show()
        self.app.run()


if __name__ == "__main__":

    with open("data/twisted_rods/rod1_position.npy", "rb") as f:
        rod1_position = np.load(f).astype(np.float32)

    with open("data/twisted_rods/rod1_radius.npy", "rb") as f:
        rod1_radius = np.load(f).astype(np.float32)

    with open("data/twisted_rods/rod1_time.npy", "rb") as f:
        rod1_time = np.load(f).astype(np.float32)

    with open("data/twisted_rods/rod2_position.npy", "rb") as f:
        rod2_position = np.load(f).astype(np.float32)

    with open("data/twisted_rods/rod2_radius.npy", "rb") as f:
        rod2_radius = np.load(f).astype(np.float32)

    with open("data/twisted_rods/rod2_time.npy", "rb") as f:
        rod2_time = np.load(f).astype(np.float32)

    example_visualization_dict = {
        "objects": {
            "rod1": {
                "type": "rod",
                "position": rod1_position,
                "radius": rod1_radius,
                "closed": False,
                "color": "green",
            },
            "rod2": {
                "type": "rod",
                "position": rod2_position,
                "radius": rod2_radius,
                "closed": False,
                "color": "violet",
            },
        },
        "time": rod1_time,
    }

    print(example_visualization_dict.keys())

    # print(example_visualization_dict["objects"]["rod1"]["position"].shape)
    Visualizer = Visualizer(example_visualization_dict)
    # Visualizer.run()
