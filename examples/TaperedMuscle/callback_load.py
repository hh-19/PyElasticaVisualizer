from examples.dMRI_Trackography.trackogram_rods_postprocessing import (
    generate_video_fury, make_fury_video,view_w_fury)
import pickle
import numpy as np
from collections import defaultdict


# pos = dict()
# for id in range(len(pp_list)):
#     pos[id] = np.array(pp_list["rod" + str(id)]["position"])

master_dict = defaultdict(list)

for rod_id in range(10):
    master_dict["rod" + str(rod_id)] = {}
    for time_id in range(100):
        with open('callbacks/callback_%04d_%05d.p' % (rod_id, time_id), 'rb') as fp:
            master_dict["rod" + str(rod_id)]["time"] = []
            master_dict["rod" + str(rod_id)]["step"]=[]
            master_dict["rod" + str(rod_id)]["position"]=[]
            master_dict["rod" + str(rod_id)]["velocity"]=[]
            master_dict["rod" + str(rod_id)]["avg_velocity"]=[]
            master_dict["rod" + str(rod_id)]["center_of_mass"]=[]


for rod_id in range(10):
    for time_id in range(100):
        with open('callbacks/callback_%04d_%05d.p' % (rod_id, time_id), 'rb') as fp:
            temp_dict = pickle.load(fp)
            master_dict["rod" + str(rod_id)]["time"].append(temp_dict['time'])
            master_dict["rod" + str(rod_id)]["step"].append(temp_dict["step"])
            master_dict["rod" + str(rod_id)]["position"].append(temp_dict["position"])
            master_dict["rod" + str(rod_id)]["velocity"].append(temp_dict["velocity"])
            master_dict["rod" + str(rod_id)]["avg_velocity"].append(temp_dict["avg_velocity"])
            master_dict["rod" + str(rod_id)]["center_of_mass"].append(temp_dict["center_of_mass"])

pos = dict()
for id in range(len(master_dict)):
    pos[id] = np.array(master_dict["rod" + str(id)]["position"])

# view_w_fury(pos,start=0,end=100)
generate_video_fury(pos,start=0,end=100,fname='temp_img')