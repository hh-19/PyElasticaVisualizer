# PyElasticaVisualizer

A visualizing toolkit for PyElastica. Still a continuing work in progress so features will continue to be added and compatability cannot be guaranteed.

## Usage

The visualizer tool is designed to work with data produced by PyElastica simulations through its callback functionality. For the quickest way to get a bare-bones visualization of a simulation working:

1. Collect simulation diagnostics using `VisualizerDictCallBack` from `utils.py`

    ```
    postprocessing_dict = {"object1": defaultdict(list),
                           "object2": defaultdict(list),
                           ...
                           }

    pyelastica_sim.collect_diagnostics(object1).using(
    VisualizerDictCallBack, step_skip=50, callback_params=postprocessing_dict["object1"]
    )

    pyelastica_sim.collect_diagnostics(object1).using(
    VisualizerDictCallBack, step_skip=50, callback_params=postprocessing_dict["object1"]
    )

    ...

    ```
    Note the `VisualizerDictCallBack` must be attached to each object in the system, so it can be cumbersome when there are many objects in a system.

    The postprocessing dict must also be specified as done above.

2. Using 

