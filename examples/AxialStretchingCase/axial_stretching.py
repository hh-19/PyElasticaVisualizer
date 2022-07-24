""" Axial stretching test-case

    Assume we have a rod lying aligned in the x-direction, with high internal
    damping.

    We fix one end (say, the left end) of the rod to a wall. On the right
    end we apply a force directed axially pulling the rods tip. Linear
    theory (assuming small displacements) predict that the net displacement
    experienced by the rod tip is Δx = FL/AE where the symbols carry their
    usual meaning (the rod is just a linear spring). We compare our results
    with the above result.

    We can "improve" the theory by having a better estimate for the rod's
    spring constant by assuming that it equilibriates under the new position,
    with
    Δx = F * (L + Δx)/ (A * E)
    which results in Δx = (F*l)/(A*E - F). Our rod reaches equilibrium wrt to
    this position.

    Note that if the damping is not high, the rod oscillates about the eventual
    resting position (and this agrees with the theoretical predictions without
    any damping : we should see the rod oscillating simple-harmonically in time).

    isort:skip_file
"""
# FIXME without appending sys.path make it more generic
import sys

sys.path.append("../../")  # isort:skip
sys.path.insert(0, "")

# from collections import defaultdict

import numpy as np
from matplotlib import pyplot as plt

from elastica import *
from visualizer import Visualizer
from utils import generate_visualization_dict, VisualizerDictCallBack

class StretchingBeamSimulator(BaseSystemCollection, Constraints, Forcing, CallBacks):
    pass


stretch_sim = StretchingBeamSimulator()
final_time = 20.0

# Options
PLOT_FIGURE = True
SAVE_FIGURE = False
SAVE_RESULTS = False
VISUALIZE = True

# setting up test params
n_elem = 19
start = np.zeros((3,))
direction = np.array([1.0, 0.0, 0.0])
normal = np.array([0.0, 1.0, 0.0])
base_length = 1.0
base_radius = 0.025
base_area = np.pi * base_radius ** 2
density = 1000
nu = 2.0
youngs_modulus = 1e4
# For shear modulus of 1e4, nu is 99!
poisson_ratio = 0.5
shear_modulus = youngs_modulus / (poisson_ratio + 1.0)

stretchable_rod = CosseratRod.straight_rod(
    n_elem,
    start,
    direction,
    normal,
    base_length,
    base_radius,
    density,
    nu,
    youngs_modulus,
    shear_modulus=shear_modulus,
)

stretch_sim.append(stretchable_rod)
stretch_sim.constrain(stretchable_rod).using(
    OneEndFixedBC, constrained_position_idx=(0,), constrained_director_idx=(0,)
)

end_force_x = 1.0
end_force = np.array([end_force_x, 0.0, 0.0])
stretch_sim.add_forcing_to(stretchable_rod).using(
    EndpointForces, 0.0 * end_force, end_force, ramp_up_time=1e-2
)

# Add call backs
class AxialStretchingCallBack(CallBackBaseClass):
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
            # Collect only x
            self.callback_params["position"].append(
                system.position_collection[0, -1].copy()
            )
            return


recorded_history = defaultdict(list)
stretch_sim.collect_diagnostics(stretchable_rod).using(
    AxialStretchingCallBack, step_skip=200, callback_params=recorded_history
)

postprocessing_dict = {"stretchable_rod": defaultdict(list)}

stretch_sim.collect_diagnostics(stretchable_rod).using(
    VisualizerDictCallBack, step_skip=200, callback_params=postprocessing_dict["stretchable_rod"]
)

stretch_sim.finalize()
timestepper = PositionVerlet()
# timestepper = PEFRL()

dl = base_length / n_elem
dt = 0.01 * dl
total_steps = int(final_time / dt)
print("Total steps", total_steps)
integrate(timestepper, stretch_sim, final_time, total_steps)

############################### Visualizing ###############################

if VISUALIZE:

    visualization_dict = generate_visualization_dict(postprocessing_dict)
    Visualizer = Visualizer(visualization_dict)
    Visualizer.run()

###########################################################################

if PLOT_FIGURE:
    # First-order theory with base-length
    expected_tip_disp = end_force_x * base_length / base_area / youngs_modulus
    # First-order theory with modified-length, gives better estimates
    expected_tip_disp_improved = (
        end_force_x * base_length / (base_area * youngs_modulus - end_force_x)
    )

    fig = plt.figure(figsize=(10, 8), frameon=True, dpi=150)
    ax = fig.add_subplot(111)
    ax.plot(recorded_history["time"], recorded_history["position"], lw=2.0)
    ax.hlines(base_length + expected_tip_disp, 0.0, final_time, "k", "dashdot", lw=1.0)
    ax.hlines(
        base_length + expected_tip_disp_improved, 0.0, final_time, "k", "dashed", lw=2.0
    )
    if SAVE_FIGURE:
        fig.savefig("axial_stretching.pdf")
    plt.show()

if SAVE_RESULTS:
    import pickle

    filename = "examples/AxialStrechingCase/axial_stretching_data.dat"
    file = open(filename, "wb")
    pickle.dump(stretchable_rod, file)
    file.close()
