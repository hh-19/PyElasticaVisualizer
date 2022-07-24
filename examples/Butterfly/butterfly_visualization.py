"""
Visualizes the butterfly simulation from saved data
"""

import pickle
import sys

sys.path.insert(0, "")

from visualizer import Visualizer
from utils import generate_visualization_dict

with open("examples/butterfly/butterfly_data.dat", "rb") as f:
    postprocessing_dict = pickle.load(f)

grouping_parameters = {
    "rod_group": {
        "object_type": "rod",
        "objects": ["butterfly_rod"],
        "color": "green",
        "closed": False
    }
}

visualization_dict = generate_visualization_dict(postprocessing_dict, grouping_parameters)

Visualizer = Visualizer(visualization_dict)
Visualizer.run()