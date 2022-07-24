__doc__ = """Timoshenko beam validation case, for detailed explanation refer to 
Gazzola et. al. R. Soc. 2018  section 3.4.3 """

import numpy as np
import sys

# FIXME without appending sys.path make it more generic
sys.path.append("../../")
sys.path.insert(0, "")

from elastica import *
from examples.TimoshenkoBeamCase.timoshenko_postprocessing import plot_timoshenko

from visualizer import Visualizer
from utils import generate_visualization_dict, VisualizerDictCallBack

class TimoshenkoBeamSimulator(BaseSystemCollection, Constraints, Forcing, CallBacks):
    pass


timoshenko_sim = TimoshenkoBeamSimulator()
final_time = 5000

# Options
PLOT_FIGURE = True
SAVE_FIGURE = False
SAVE_RESULTS = True
ADD_UNSHEARABLE_ROD = True
VISUALIZE = True

# setting up test params
n_elem = 100
start = np.zeros((3,))
direction = np.array([0.0, 0.0, 1.0])
normal = np.array([0.0, 1.0, 0.0])
base_length = 3.0
base_radius = 0.25
base_area = np.pi * base_radius ** 2
density = 5000
nu = 0.1
E = 1e6
# For shear modulus of 1e4, nu is 99!
poisson_ratio = 99
shear_modulus = E / (poisson_ratio + 1.0)

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

timoshenko_sim.append(shearable_rod)
timoshenko_sim.constrain(shearable_rod).using(
    OneEndFixedBC, constrained_position_idx=(0,), constrained_director_idx=(0,)
)

end_force = np.array([-15.0, 0.0, 0.0])
timoshenko_sim.add_forcing_to(shearable_rod).using(
    EndpointForces, 0.0 * end_force, end_force, ramp_up_time=final_time / 2.0
)

postprocessing_dict = {"shearable_rod": defaultdict(list)}

timoshenko_sim.collect_diagnostics(shearable_rod).using(
    VisualizerDictCallBack, step_skip=50, callback_params=postprocessing_dict["shearable_rod"]
)

if ADD_UNSHEARABLE_ROD:
    # Start into the plane
    unshearable_start = np.array([0.0, -1.0, 0.0])
    shear_modulus = E / (-0.7 + 1.0)
    unshearable_rod = CosseratRod.straight_rod(
        n_elem,
        unshearable_start,
        direction,
        normal,
        base_length,
        base_radius,
        density,
        nu,
        E,
        # Unshearable rod needs G -> inf, which is achievable with -ve poisson ratio
        shear_modulus=shear_modulus,
    )

    timoshenko_sim.append(unshearable_rod)
    timoshenko_sim.constrain(unshearable_rod).using(
        OneEndFixedBC, constrained_position_idx=(0,), constrained_director_idx=(0,)
    )
    timoshenko_sim.add_forcing_to(unshearable_rod).using(
        EndpointForces, 0.0 * end_force, end_force, ramp_up_time=final_time / 2.0
    )

    postprocessing_dict["unshearable_rod"] = defaultdict(list)
    timoshenko_sim.collect_diagnostics(unshearable_rod).using(
        VisualizerDictCallBack, step_skip=50, callback_params=postprocessing_dict["unshearable_rod"]
    )

timoshenko_sim.finalize()
timestepper = PositionVerlet()
# timestepper = PEFRL()

dl = base_length / n_elem
dt = 0.01 * dl
total_steps = int(final_time / dt)
print("Total steps", total_steps)
integrate(timestepper, timoshenko_sim, final_time, total_steps)

if SAVE_RESULTS:
    import pickle

    filename = "examples/TimoshenkoBeamCase/timoshenko_beam_data.dat"
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
    plot_timoshenko(shearable_rod, end_force, SAVE_FIGURE, ADD_UNSHEARABLE_ROD)