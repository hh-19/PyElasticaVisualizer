__doc__ = """Helical buckling validation case, for detailed explanation refer to 
Gazzola et. al. R. Soc. 2018  section 3.4.1 """

import numpy as np
import sys

# FIXME without appending sys.path make it more generic
sys.path.append("../../")
sys.path.insert(0, "")

from elastica import *
from examples.HelicalBucklingCase.helicalbuckling_postprocessing import (
    plot_helicalbuckling,
)
from visualizer import Visualizer
from utils import generate_visualization_dict, VisualizerDictCallBack

class HelicalBucklingSimulator(BaseSystemCollection, Constraints, Forcing, CallBacks):
    pass


helicalbuckling_sim = HelicalBucklingSimulator()

# Options
PLOT_FIGURE = True
SAVE_FIGURE = False
SAVE_RESULTS = True
VISUALIZE = True

# setting up test params
n_elem = 100
start = np.zeros((3,))
direction = np.array([0.0, 0.0, 1.0])
normal = np.array([0.0, 1.0, 0.0])
base_length = 100.0
base_radius = 0.35
base_area = np.pi * base_radius ** 2
density = 1.0 / (base_area)
nu = 0.01
E = 1e6
slack = 3
number_of_rotations = 27
# For shear modulus of 1e5, nu is 99!
poisson_ratio = 9
shear_modulus = E / (poisson_ratio + 1.0)
shear_matrix = np.repeat(
    shear_modulus * np.identity((3))[:, :, np.newaxis], n_elem, axis=2
)
temp_bend_matrix = np.zeros((3, 3))
np.fill_diagonal(temp_bend_matrix, [1.345, 1.345, 0.789])
bend_matrix = np.repeat(temp_bend_matrix[:, :, np.newaxis], n_elem - 1, axis=2)

shearable_rod = CosseratRod.straight_rod(
    n_elem,
    start,
    direction,
    normal,
    base_length,
    base_radius,
    density,
    nu,
    E,
    shear_modulus=shear_modulus,
)
# TODO: CosseratRod has to be able to take shear matrix as input, we should change it as done below

shearable_rod.shear_matrix = shear_matrix
shearable_rod.bend_matrix = bend_matrix


helicalbuckling_sim.append(shearable_rod)
helicalbuckling_sim.constrain(shearable_rod).using(
    HelicalBucklingBC,
    constrained_position_idx=(0, -1),
    constrained_director_idx=(0, -1),
    twisting_time=500,
    slack=slack,
    number_of_rotations=number_of_rotations,
)

postprocessing_dict = {"shearable_rod": defaultdict(list)}
helicalbuckling_sim.collect_diagnostics(shearable_rod).using(
    VisualizerDictCallBack, step_skip=500, callback_params=postprocessing_dict["shearable_rod"]
)

helicalbuckling_sim.finalize()
timestepper = PositionVerlet()
shearable_rod.velocity_collection[..., int((n_elem) / 2)] += np.array([0, 1e-6, 0.0])
# timestepper = PEFRL()

final_time = 10500.0
dl = base_length / n_elem
dt = 1e-3 * dl
total_steps = int(final_time / dt)

print("Total steps", total_steps)

integrate(timestepper, helicalbuckling_sim, final_time, total_steps)

if SAVE_RESULTS:
    import pickle

    filename = "examples/HelicalBucklingCase/helical_buckling_postprocessing_data.dat"
    file = open(filename, "wb")
    pickle.dump(postprocessing_dict, file)
    file.close()

############################### Visualizing ###############################

if VISUALIZE:

    visualization_dict = generate_visualization_dict(postprocessing_dict)
    Visualizer = Visualizer(visualization_dict)
    Visualizer.run()

###########################################################################

if PLOT_FIGURE:
    plot_helicalbuckling(shearable_rod, SAVE_FIGURE)


