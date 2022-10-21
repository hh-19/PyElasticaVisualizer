""" 
Will add more examples, here is an example of how visualization can be added to an existing pyelastica simulation script.
The only main steps are callback and the visualization, which are marked below. Should be plug and play for any other
simulations, let me know how you get on for more involved and complicated simulations:) 
"""
# FIXME without appending sys.path make it more generic
import sys

sys.path.append("../../")  # isort:skip
sys.path.insert(0, "")

import numpy as np
from matplotlib import pyplot as plt

from elastica import *
from qt_visualizer import VisualizerGUI, CanvasWrapper
from utils import generate_visualization_dict, VisualizerDictCallBack

class SwingingFlexiblePendulumSimulator(
    BaseSystemCollection, Constraints, Forcing, CallBacks
):
    pass


# Options
PLOT_FIGURE = False
PLOT_VIDEO = False
SAVE_FIGURE = False
SAVE_RESULTS = False
VISUALIZE = True

# For 10 elements, the prefac is  0.0007
pendulum_sim = SwingingFlexiblePendulumSimulator()
final_time = 1.0 if SAVE_RESULTS else 5.0

# setting up test params
n_elem = 10 if SAVE_RESULTS else 50
start = np.zeros((3,))
direction = np.array([0.0, 0.0, 1.0])
normal = np.array([1.0, 0.0, 0.0])
base_length = 1.0
base_radius = 0.005
base_area = np.pi * base_radius ** 2
density = 1100.0
nu = 0.0
youngs_modulus = 5e6
# For shear modulus of 1e4, nu is 99!
poisson_ratio = 0.5

pendulum_rod = CosseratRod.straight_rod(
    n_elem,
    start,
    direction,
    normal,
    base_length,
    base_radius,
    density,
    nu,
    youngs_modulus,
    shear_modulus=youngs_modulus / (poisson_ratio + 1.0),
)

pendulum_sim.append(pendulum_rod)


# Bad name : whats a FreeRod anyway?
class HingeBC(ConstraintBase):
    """
    the end of the rod fixed x[0]
    """

    def __init__(self, fixed_position, fixed_directors, **kwargs):
        super().__init__(**kwargs)
        self.fixed_position = np.array(fixed_position)
        self.fixed_directors = np.array(fixed_directors)

    def constrain_values(self, rod, time):
        rod.position_collection[..., 0] = self.fixed_position

    def constrain_rates(self, rod, time):
        rod.velocity_collection[..., 0] = 0.0


pendulum_sim.constrain(pendulum_rod).using(
    HingeBC, constrained_position_idx=(0,), constrained_director_idx=(0,)
)

# Add gravitational forces
gravitational_acc = -9.80665
pendulum_sim.add_forcing_to(pendulum_rod).using(
    GravityForces, acc_gravity=np.array([gravitational_acc, 0.0, 0.0])
)


# Add call backs
class PendulumCallBack(CallBackBaseClass):
    """
    Call back function for continuum snake
    """

    def __init__(self, step_skip: int, callback_params: dict):
        CallBackBaseClass.__init__(self)
        self.every = step_skip
        self.callback_params = callback_params

    def make_callback(self, system, time, current_step: int):
        if current_step % self.every == 0:
            self.callback_params["time"].append(time)
            self.callback_params["position"].append(system.position_collection.copy())
            self.callback_params["directors"].append(system.director_collection.copy())
            if time > 0.0:
                self.callback_params["internal_stress"].append(
                    system.internal_stress.copy()
                )
                self.callback_params["internal_couple"].append(
                    system.internal_couple.copy()
                )
        return


dl = base_length / n_elem
dt = (0.0007 if SAVE_RESULTS else 0.002) * dl
total_steps = int(final_time / dt)

print("Total steps", total_steps)
recorded_history = defaultdict(list)
step_skip = (
    60
    if PLOT_VIDEO
    else (int(total_steps / 10) if PLOT_FIGURE else int(total_steps / 200))
)
pendulum_sim.collect_diagnostics(pendulum_rod).using(
    PendulumCallBack, step_skip=step_skip, callback_params=recorded_history
)

############################## Callback #####################################
# Postprocessing dict for visualization
postprocessing_dict = {"pendulum_rod": defaultdict(list)}
pendulum_sim.collect_diagnostics(pendulum_rod).using(
    VisualizerDictCallBack, step_skip=step_skip, callback_params=postprocessing_dict["pendulum_rod"]
)
#############################################################################

pendulum_sim.finalize()
timestepper = PositionVerlet()

integrate(timestepper, pendulum_sim, final_time, total_steps)

############################### Visualizing ###############################

if VISUALIZE:

    visualization_dict = generate_visualization_dict(postprocessing_dict)
    canvas = CanvasWrapper(visualization_dict)
    canvas.add_axis("z")
    canvas.add_axis("x")
    canvas.turntable_camera()

    Visualizer = VisualizerGUI(visualization_dict, canvas)
    Visualizer.run()

###########################################################################
