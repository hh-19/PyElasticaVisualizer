"""
Visualizes the continuum snake from saved data
"""

import pickle
import sys

sys.path.insert(0, "")

from visualizer import Visualizer
from utils import generate_visualization_dict

with open("examples/ContinuumSnakeCase/continuum_snake.dat", "rb") as f:
    postprocessing_dict = pickle.load(f)

visualization_dict = generate_visualization_dict(postprocessing_dict)

Visualizer = Visualizer(visualization_dict)
Visualizer.run()