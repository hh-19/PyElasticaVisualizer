# PyElasticaVisualizer

A visualizing toolkit for PyElastica developed as part of the work undetaken in GSoC 2022. Still a continuing work in progress so features will continue to be added and compatability cannot be guaranteed.

## Instalation

`PyElasticaVisualizer` uses [Poetry](https://python-poetry.org/docs/) for its dependency management, like `PyElastica`. With potetry installed, to run your visualization script, simply use `poetry run python your_script.py`.

## Usage

The visualizer tool is designed to work with data produced by PyElastica simulations through its callback functionality. For the quickest way to get a bare-bones visualization of a simulation working:

1. Collect simulation diagnostics using `VisualizerDictCallBack` from `utils.py`

    ```python
    postprocessing_dict = {"object1": defaultdict(list),
                           "object2": defaultdict(list),
                           ...
                           }

    pyelastica_sim.collect_diagnostics(object1).using(
    VisualizerDictCallBack, step_skip=step_skip, callback_params=postprocessing_dict["object1"]
    )

    pyelastica_sim.collect_diagnostics(object2).using(
    VisualizerDictCallBack, step_skip=step_skip, callback_params=postprocessing_dict["object2"]
    )

    ...

    ```

    Note the `VisualizerDictCallBack` must be attached to each object in the system, so it can be cumbersome when there are many objects in a system.

    The postprocessing dict must also be specified as done above.

2. Use the `generate_visualization_dict` function from `utils.py` to reformat postprocessing dictionary into the correct format to pass to the Visualizer

    ```python
    visualization_dict = generate_visualization_dict(postprocessing_dict, grouping_parameters=None)
    ```

    The purpose of the visualization dicitionary is to have a defined standard for passing simulation data and visualization parameters to the visualizer.

    `grouping_parameters` is a dictionary passed to the function that can be used to specify groups of objects in the simulation and define paramters for this group to be used when visualizing these objects eg. color, level of detail etc.
    The format is likely to change a lot as more features are added to visualizer.

3. Initialise and run the visualizer.
There are two possible visualizers that can be used at the current moment the `Visualizer` class in `visualizer.py` and `VisualizerGUI` class in `qt_visualizer.py`. The `Visualizer` class is only the Vispy canvas, while `VisualizerGUI` is the Vispy canvas emedded into a GUI made with QT. The `VisualizerGUI` embedded canvas has all the features of the standalone visualization canvas; the only reason for the existence of the base `Visualizer` is that it is better for saving the visualization as a video file, however, this is planned to be implemented in the `VisualizerGUI` class shortly.

    Using the `Visualizer` class:

    ```python
    Visualizer = Visualizer(visualization_dict)
    Visualizer.add_axis('x') # Example of adding an axis to the scene
    Visualizer.add_axis('z')
    Visualizer.turntable_camera() # Sets a camera type 
    Visualizer.run()
    ```

    Using the `VisualizerGUI` class:

    ```python
    canvas = CanvasWrapper(visualization_dict)
    canvas.add_axis("z")
    canvas.add_axis("x")
    canvas.turntable_camera()

    Visualizer = VisualizerGUI(visualization_dict, canvas)
    Visualizer.run()
    ```

This is an ongoing project that is intended to be developed after GSoC, and there will be new features and improvements in the future.

There are a several PyElastica example simulations in the `examples/` directory which have been modified to be visualized, and can be used as examples.
