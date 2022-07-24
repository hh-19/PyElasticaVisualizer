"""
NOTE:

This whole bit in getting the data out of the PyElastica simulation into a defined format
that can be passed to the Visualizer is quite messy. We need a format and utils that allows for ease in
getting a Visualization up and running quickly that does not require the user to spend 
time tinkering with stuff, while still allowing for user control over how the Visualization 
looks if required.

This is definitely not intuitive, it kind of allows for quick Visualization 
but not sure if this is the best way, and if it isn't then what is.

Example of grouping_parameters_dictionary:

grouping_parameters = {
    "rod_group": {
        "object_type": "rod"
        "objects": ["rod1", "rod2"]
        "color": "green"
        "closed": False
    }
}
"""

from elastica import CallBackBaseClass

def generate_visualization_dict(postprocessing_dict, grouping_parameters=None):
    """ Generates a dictionary in the required format to be passed to the Visualizer
    
    TODO: Improve the default grouping parameter for when no grouping parameters are passed

    Args:
        postprocessing_dict (dict): Dictionary of system parameters outputted by PyEastica callback
        grouping_parameters (dict): Grouping parameters used to group objects in the simulation 
        together to easily control various visualization parameters for all object in the group
    
    Returns:
        visualization_dict (dict): Visualization dict in the right format to be passed to the Visualizer
    
    Output should be like 
    
    example_visualization_dict = {
        "rod1": {
            "type": "rod",
            "position": rod1_position,
            "radius": rod1_radius,
            "closed": False,
            "color": "green",
        },
        "rod2": {
            ...
        },
        "time": time
    }
    """

    visualization_dict = {"objects": {}}

    if grouping_parameters is None:

        objects = list(postprocessing_dict.keys())

        grouping_parameters = {"all_objects": {
                            "object_type": "rod",
                            "objects": objects,
                            "color": "green",
                            "closed": False}}
        
    for group in grouping_parameters:

        object_type = grouping_parameters[group]["object_type"]
        objects = grouping_parameters[group]["objects"]
        color = grouping_parameters[group]["color"]
        closed = grouping_parameters[group]["closed"]

        for object in objects:

            visualization_dict["objects"][object] = {
                "type": object_type,
                "position": postprocessing_dict[object]["position"],
                "radius": postprocessing_dict[object]["radius"],
                "color": color,
                "closed": closed
            }

        visualization_dict["time"] = postprocessing_dict[object]["time"] 
    return visualization_dict

class VisualizerDictCallBack(CallBackBaseClass):
    """
    Call back function to output simulation data into postprocessing dict
    Post-processing dict attached to the callback should be of the form:

    postprocessing_dict = {"object_1": defaultdict(list),
                           "object_2": defaultdict(list),
                           ...
                           }
    
    to work as seamlessly as possible with rest of the util functions and the
    Visualizer class
    """

    def __init__(self, step_skip: int, callback_params: dict):
        CallBackBaseClass.__init__(self)
        self.every = step_skip
        self.callback_params = callback_params

    def make_callback(self, system, time, current_step: int):

        if current_step % self.every == 0:

            self.callback_params["time"].append(time)
            self.callback_params["position"].append(system.position_collection.copy())
            self.callback_params["radius"].append(system.radius.copy())
            return