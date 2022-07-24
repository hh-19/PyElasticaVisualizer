# FIXME without appending sys.path make it more generic
import sys

sys.path.append("../")
sys.path.append("../../")

sys.path.insert(0, "")


# from collections import defaultdict
import numpy as np

from elastica import *
from elastica.utils import MaxDimension

from visualizer import Visualizer
from utils import generate_visualization_dict, VisualizerDictCallBack

class ButterflySimulator(BaseSystemCollection, CallBacks):
    pass


butterfly_sim = ButterflySimulator()
final_time = 40.0

# Options
SAVE_RESULTS = False
ADD_UNSHEARABLE_ROD = False

# setting up test params
# FIXME : Doesn't work with elements > 10 (the inverse rotate kernel fails)
n_elem = 4  # Change based on requirements, but be careful
n_elem += n_elem % 2
half_n_elem = n_elem // 2

origin = np.zeros((3, 1))
angle_of_inclination = np.deg2rad(45.0)

# in-plane
horizontal_direction = np.array([0.0, 0.0, 1.0]).reshape(-1, 1)
vertical_direction = np.array([1.0, 0.0, 0.0]).reshape(-1, 1)

# out-of-plane
normal = np.array([0.0, 1.0, 0.0])

total_length = 3.0
base_radius = 0.25
base_area = np.pi * base_radius ** 2
density = 5000
nu = 0.0
youngs_modulus = 1e4
poisson_ratio = 0.5
shear_modulus = youngs_modulus / (poisson_ratio + 1.0)

positions = np.empty((MaxDimension.value(), n_elem + 1))
dl = total_length / n_elem

# First half of positions stem from slope angle_of_inclination
first_half = np.arange(half_n_elem + 1.0).reshape(1, -1)
positions[..., : half_n_elem + 1] = origin + dl * first_half * (
    np.cos(angle_of_inclination) * horizontal_direction
    + np.sin(angle_of_inclination) * vertical_direction
)
positions[..., half_n_elem:] = positions[
    ..., half_n_elem : half_n_elem + 1
] + dl * first_half * (
    np.cos(angle_of_inclination) * horizontal_direction
    - np.sin(angle_of_inclination) * vertical_direction
)

butterfly_rod = CosseratRod.straight_rod(
    n_elem,
    start=origin.reshape(3),
    direction=np.array([0.0, 0.0, 1.0]),
    normal=normal,
    base_length=total_length,
    base_radius=base_radius,
    density=density,
    nu=nu,
    youngs_modulus=youngs_modulus,
    shear_modulus=shear_modulus,
    position=positions,
)

butterfly_sim.append(butterfly_rod)

postprocessing_dict = {"butterfly_rod": defaultdict(list)}

butterfly_sim.collect_diagnostics(butterfly_rod).using(
    VisualizerDictCallBack, step_skip=50, callback_params=postprocessing_dict["butterfly_rod"]
)

butterfly_sim.finalize()
timestepper = PositionVerlet()

dt = 0.01 * dl
total_steps = int(final_time / dt)
print("Total steps", total_steps)
integrate(timestepper, butterfly_sim, final_time, total_steps)

if SAVE_RESULTS:
    import pickle

    print(postprocessing_dict)
    filename = "examples/butterfly/butterfly_data.dat"
    file = open(filename, "wb")
    pickle.dump(postprocessing_dict, file)
    file.close()


############################### Visualizing ###############################

visualization_dict = generate_visualization_dict(postprocessing_dict)

Visualizer = Visualizer(visualization_dict)
Visualizer.run()
