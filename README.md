# PyElasticaVisualizer

A visualizing toolkit for PyElastica. Still a continuing work in progress so features will continue to be added and compatability cannot be guaranteed.

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

    `grouping_parameters` is a dictionary passed to the function that can be used to specify groups of objects in the simulation and define paramters for this group to be used when visualizing these objects eg. color, level of detail etc.
    The format is likely to change a lot as more features are added to visualizer.

3. Initialise and run the visualizer

    ```python
    Visualizer = Visualizer(visualization_dict)
    Visualizer.run()
    ```

There are a several PyElastica example simulations in the `examples/` directory which have been modified to be visualized, and can be used as examples.
