"""
Visualizes the tapered muscle simulation from saved data
Visualization workflow is a bit different due to the way 
that data is saved

"""
import sys
import numpy as np

sys.path.insert(0, "")

from visualizer import Visualizer
from utils import generate_visualization_dict

if __name__ == "__main__":
    data = np.load("examples/TaperedMuscle/tapered_nine_muscle_rods.npz")
    # print(data["straight_rods_position_history"].shape)
    # print(data["straight_rods_radius_history"].shape)
    # print(data["inner_ring_rods_radius_history"].shape)
    # print(data["inner_ring_rods_position_history"].shape)

    tapered_muscle_visualization_dict = {
        "objects": {
            "rod1": {
                "type": "rod",
                "position": data["straight_rods_position_history"][0],
                "radius": data["straight_rods_radius_history"][0],
                "closed": False,
                "color": "green",
            },
            "rod2": {
                "type": "rod",
                "position": data["straight_rods_position_history"][1],
                "radius": data["straight_rods_radius_history"][1],
                "closed": False,
                "color": "green",
            },
            "rod3": {
                "type": "rod",
                "position": data["straight_rods_position_history"][2],
                "radius": data["straight_rods_radius_history"][2],
                "closed": False,
                "color": "green",
            },
            "rod4": {
                "type": "rod",
                "position": data["straight_rods_position_history"][3],
                "radius": data["straight_rods_radius_history"][3],
                "closed": False,
                "color": "green",
            },
            "rod5": {
                "type": "rod",
                "position": data["straight_rods_position_history"][4],
                "radius": data["straight_rods_radius_history"][4],
                "closed": False,
                "color": "green",
            },
            "rod6": {
                "type": "rod",
                "position": data["straight_rods_position_history"][5],
                "radius": data["straight_rods_radius_history"][5],
                "closed": False,
                "color": "green",
            },
            "rod7": {
                "type": "rod",
                "position": data["straight_rods_position_history"][6],
                "radius": data["straight_rods_radius_history"][6],
                "closed": False,
                "color": "green",
            },
            "rod8": {
                "type": "rod",
                "position": data["straight_rods_position_history"][7],
                "radius": data["straight_rods_radius_history"][7],
                "closed": False,
                "color": "green",
            },
            "inner_ring_1": {
                "type": "rod",
                "position": data["inner_ring_rods_position_history"][0],
                "radius": data["inner_ring_rods_radius_history"][0],
                "closed": True,
                "color": "purple",
            },
            "inner_ring_2": {
                "type": "rod",
                "position": data["inner_ring_rods_position_history"][9],
                "radius": data["inner_ring_rods_radius_history"][9],
                "closed": True,
                "color": "purple",
            },
            "inner_ring_3": {
                "type": "rod",
                "position": data["inner_ring_rods_position_history"][19],
                "radius": data["inner_ring_rods_radius_history"][19],
                "closed": True,
                "color": "purple",
            },
            "inner_ring_4": {
                "type": "rod",
                "position": data["inner_ring_rods_position_history"][29],
                "radius": data["inner_ring_rods_radius_history"][29],
                "closed": True,
                "color": "purple",
            },
            "inner_ring_5": {
                "type": "rod",
                "position": data["inner_ring_rods_position_history"][39],
                "radius": data["inner_ring_rods_radius_history"][39],
                "closed": True,
                "color": "purple",
            },
            "outer_ring_1": {
                "type": "rod",
                "position": data["outer_ring_rods_position_history"][0],
                "radius": data["outer_ring_rods_radius_history"][0],
                "closed": True,
                "color": "blue",
            },
            "outer_ring_2": {
                "type": "rod",
                "position": data["outer_ring_rods_position_history"][9],
                "radius": data["outer_ring_rods_radius_history"][9],
                "closed": True,
                "color": "blue",
            },
            "outer_ring_3": {
                "type": "rod",
                "position": data["outer_ring_rods_position_history"][19],
                "radius": data["outer_ring_rods_radius_history"][19],
                "closed": True,
                "color": "blue",
            },
            "outer_ring_4": {
                "type": "rod",
                "position": data["outer_ring_rods_position_history"][29],
                "radius": data["outer_ring_rods_radius_history"][29],
                "closed": True,
                "color": "blue",
            },
            "outer_ring_5": {
                "type": "rod",
                "position": data["outer_ring_rods_position_history"][39],
                "radius": data["outer_ring_rods_radius_history"][39],
                "closed": True,
                "color": "blue",
            },
        },
        "time": data["time"]
    }
    
    Visualizer = Visualizer(tapered_muscle_visualization_dict)
    # Visualizer.run(video_fname="examples/TaperedMuscle/tapered_nine_muscle_rods_visualization.mp4")