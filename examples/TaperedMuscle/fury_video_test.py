# from examples.dMRI_Trackography.trackogram_rods_postprocessing import (
#     generate_video_fury, make_fury_video,view_w_fury)
import pickle
import numpy as np
from fury import window, actor


def main():
	data = np.load("tapered_nine_muscle_rods.npz")
	(time_list, 
		straight_rods_position_history, straight_rods_radius_history, 
		inner_ring_rods_position_history, inner_ring_rods_radius_history, 
		outer_ring_rods_position_history, outer_ring_rods_radius_history) = (data['time'], data['straight_rods_position_history'],data['straight_rods_radius_history'], data['inner_ring_rods_position_history'], 
																			data['inner_ring_rods_radius_history'], data['outer_ring_rods_position_history'], data['outer_ring_rods_radius_history'])

	# set the colors for the different groups
	color = (window.colors.white, window.colors.blue, window.colors.green, window.colors.red)
	# set the opacity for the different groups
	opacity = (1.0, 0.75, 0.5, 1.0)

	view_data = True
	save_images = False
	make_video = False


	if view_data:
		time = 0
		print(time)
		axon = (straight_rods_position_history[0,time])
		straight = (straight_rods_position_history[1:,time])
		circle_inner = inner_ring_rods_position_history[:,time]
		circle_outer = outer_ring_rods_position_history[:,time]
		stream_coll = (axon, straight,circle_outer,circle_inner)

		radius = (straight_rods_radius_history[0,time],
			straight_rods_radius_history[1:,time], 
				outer_ring_rods_radius_history[:,time], 
				inner_ring_rods_radius_history[:,time])
		print(len(stream_coll), stream_coll[0].shape )
		print(len(radius), radius[0].shape  )
		print(time)
		fury_save_files(stream_coll, radius, time, color=color, opacity=opacity, view = True)


	if save_images:
		for time in range(len(time_list)):
			print(time)
			axon = (straight_rods_position_history[0,time])
			straight = (straight_rods_position_history[1:,time])
			circle_inner = inner_ring_rods_position_history[:,time]
			circle_outer = outer_ring_rods_position_history[:,time]
			stream_coll = (axon, straight,circle_outer,circle_inner)

			radius = (straight_rods_radius_history[0,time],
				straight_rods_radius_history[1:,time], 
					outer_ring_rods_radius_history[:,time], 
					inner_ring_rods_radius_history[:,time])
			
			fury_save_files(stream_coll, radius, time, color=color, opacity=opacity, view = False)


	if make_video:
		make_fury_video()

# view_w_fury(pos,0,1)


# In this example, callback_data is a dict with entries for each rod.
def fury_save_files(stream_coll, radius, time, color, opacity, view = True):
	# initalize viewer
	ren = window.Scene()

	# optional: set camera position. You can also get the camera position
	# with print(ren.get_camera()) after manipulating it in the viewer.
	# position = (17.14, 52.24, 2.97)
	# focal_pt = (0.98, 4.65, 3.52)
	# view_up = (-0.03, 0.18, -0.58)
	position, focal_pt, view_up = (
									(7.71357108132753e-06, 0.4999510228569592, 6.9036315905697665), 
									(7.71357108132753e-06, 0.4999510228569592, 0.0), 
									(0.0, 1.0, 0.0))

	# Make list of rods/streamlines centerline postions.
	# Rods should be np array of size [N,3]

	# generate color scheme. For all one color, can use `window.colors.red`
	# colormapping = actor.create_colormap(np.arange(len(stream_coll)))
	

	# ren.SetBackground(0, 0, 0) # set black background (default)
	# ren.SetBackground(1, 1, 1) # set white background

	# add streamtubes to ren
	# print(radii_array)

	# iterate through the groupings of the rods
	for n, (rods, radii) in enumerate(zip(stream_coll, radius)):
		# iterate through each rod in the grouping
		num_rods = rods.shape[0] if rods.ndim == 3 else 1
		for i in range(num_rods):
			if rods.ndim == 3:
				rod = rods[i:i+1]
				radius = radii[i]
				test = np.swapaxes(rod,1,2)

			else:
				rod = rods
				radius = radii
				test = np.swapaxes(rod,0,1)
				test = test[None,:,:] #Add a blank axis since there is  only 1 rod in this group.     		
			
			# axon and straight muscles should have a cap on them, ring rods should not
			if n <= 1:
				st = streamtube(test, radii_array = radius, colors = color[n], opacity=opacity[n], )
			else:
				st = streamtube(test, radii_array = radius, colors = color[n], opacity=opacity[n], remove_cap=True)
			ren.add(st)

	# optional: set camera position
	ren.set_camera(position=position, focal_point=focal_pt, view_up=view_up)
	

	# display interactive window viewer
	if view:
		window.show(ren)
		print(ren.get_camera())
	else:
		fname='file'
		# save image
		window.record(ren, out_path="temp_imgs/%s%02d.png" % (fname, time), size=(512, 512))

	# optional: remove all objects in ren
	ren.clear()

def make_fury_video():
	import os
	import subprocess
	import glob
	os.chdir("temp_imgs")
	subprocess.call([
		'ffmpeg', '-framerate', '20', '-i', 'file%02d.png', '-r', '30', '-pix_fmt', 'yuv420p',
		'../full_sim_video2.mp4'
	])
	# for file_name in glob.glob("*.png"):
	#     os.remove(file_name)

import os.path as op
import numpy as np
import vtk
from vtk.util import numpy_support

from fury.shaders import (load, shader_to_actor, attribute_to_actor,
						  add_shader_callback, replace_shader_in_actor)
from fury import layout
from fury.colormap import colormap_lookup_table, create_colormap, orient2rgb
from fury.deprecator import deprecated_params
from fury.utils import (lines_to_vtk_polydata, set_input, apply_affine,
						set_polydata_vertices, set_polydata_triangles, 
						numpy_to_vtk_matrix, shallow_copy, rgb_to_vtk,
						repeat_sources, get_actor_from_primitive)
from fury.io import load_image
import fury.primitive as fp



# Adapted from fury.actor.streamtube to allow varying radius of the rod
def streamtube(lines, colors=None, opacity=1, linewidth=0.1, tube_sides=20,
			   lod=True, lod_points=10 ** 4, lod_points_size=3,
			   spline_subdiv=None, lookup_colormap=None, radii_array=None, remove_cap = False):
	"""Use streamtubes to visualize polylines

	Parameters
	----------
	lines : list
		list of N curves represented as 2D ndarrays

	colors : array (N, 3), list of arrays, tuple (3,), array (K,)
		If None or False, a standard orientation colormap is used for every
		line.
		If one tuple of color is used. Then all streamlines will have the same
		colour.
		If an array (N, 3) is given, where N is equal to the number of lines.
		Then every line is coloured with a different RGB color.
		If a list of RGB arrays is given then every point of every line takes
		a different color.
		If an array (K, 3) is given, where K is the number of points of all
		lines then every point is colored with a different RGB color.
		If an array (K,) is given, where K is the number of points of all
		lines then these are considered as the values to be used by the
		colormap.
		If an array (L,) is given, where L is the number of streamlines then
		these are considered as the values to be used by the colormap per
		streamline.
		If an array (X, Y, Z) or (X, Y, Z, 3) is given then the values for the
		colormap are interpolated automatically using trilinear interpolation.

	opacity : float, optional
		Takes values from 0 (fully transparent) to 1 (opaque). Default is 1.
	linewidth : float, optional
		Default is 0.01.
	tube_sides : int, optional
		Default is 9.
	lod : bool, optional
		Use vtkLODActor(level of detail) rather than vtkActor. Default is True.
		Level of detail actors do not render the full geometry when the
		frame rate is low.
	lod_points : int, optional
		Number of points to be used when LOD is in effect. Default is 10000.
	lod_points_size : int, optional
		Size of points when lod is in effect. Default is 3.
	spline_subdiv : int, optional
		Number of splines subdivision to smooth streamtubes. Default is None.
	lookup_colormap : vtkLookupTable, optional
		Add a default lookup table to the colormap. Default is None which calls
		:func:`fury.actor.colormap_lookup_table`.

	Examples
	--------
	>>> import numpy as np
	>>> from fury import actor, window
	>>> scene = window.Scene()
	>>> lines = [np.random.rand(10, 3), np.random.rand(20, 3)]
	>>> colors = np.random.rand(2, 3)
	>>> c = actor.streamtube(lines, colors)
	>>> scene.add(c)
	>>> #window.show(scene)

	Notes
	-----
	Streamtubes can be heavy on GPU when loading many streamlines and
	therefore, you may experience slow rendering time depending on system GPU.
	A solution to this problem is to reduce the number of points in each
	streamline. In Dipy we provide an algorithm that will reduce the number of
	points on the straighter parts of the streamline but keep more points on
	the curvier parts. This can be used in the following way::

		from dipy.tracking.distances import approx_polygon_track
		lines = [approx_polygon_track(line, 0.2) for line in lines]

	Alternatively we suggest using the ``line`` actor which is much more
	efficient.

	See Also
	--------
	:func:`fury.actor.line`

	"""
	# Poly data with lines and colors
	poly_data, color_is_scalar = lines_to_vtk_polydata(lines, colors)
	next_input = poly_data

			#Add radius
	tubeRadius=vtk.vtkDoubleArray()
	tubeRadius.SetNumberOfTuples(radii_array.shape[0]+1)
	tubeRadius.SetName("TubeRadius")
	# To match the length of the stream tube I need to pad each end of the radius array. I don't know why. 
	tubeRadius.SetTuple1(0, radii_array[0])
	for i, rad in enumerate(radii_array[:-1]):
		tubeRadius.SetTuple1(i+1, rad)
	tubeRadius.SetTuple1(i+2, rad)
	next_input.GetPointData().AddArray(tubeRadius)
	next_input.GetPointData().SetActiveScalars("TubeRadius")

	# Set Normals    
	poly_normals = set_input(vtk.vtkPolyDataNormals(), next_input)
	poly_normals.ComputeCellNormalsOn()
	poly_normals.ComputePointNormalsOn()
	poly_normals.ConsistencyOn()
	poly_normals.AutoOrientNormalsOn()
	poly_normals.Update()

	next_input = poly_normals.GetOutputPort()

	# Spline interpolation
	if (spline_subdiv is not None) and (spline_subdiv > 0):
		spline_filter = set_input(vtk.vtkSplineFilter(), next_input)
		spline_filter.SetSubdivideToSpecified()
		spline_filter.SetNumberOfSubdivisions(spline_subdiv)
		spline_filter.Update()
		next_input = spline_filter.GetOutputPort()

	# Add thickness to the resulting lines
	tube_filter = set_input(vtk.vtkTubeFilter(), next_input)
	tube_filter.SetNumberOfSides(tube_sides)
	# tube_filter.SetRadius(linewidth)
	# TODO using the line above we will be able to visualize
	# streamtubes of varying radius



	tube_filter.SetVaryRadiusToVaryRadiusByAbsoluteScalar()
	if not remove_cap:
		tube_filter.CappingOn()
	tube_filter.Update()

	# tube_filter.Update()
	next_input = tube_filter.GetOutputPort()

	# Poly mapper
	poly_mapper = set_input(vtk.vtkPolyDataMapper(), next_input)
	poly_mapper.ScalarVisibilityOn()
	poly_mapper.SetScalarModeToUsePointFieldData()
	poly_mapper.SelectColorArray("colors")
	poly_mapper.Update()

	# Color Scale with a lookup table
	if color_is_scalar:
		if lookup_colormap is None:
			lookup_colormap = colormap_lookup_table()
		poly_mapper.SetLookupTable(lookup_colormap)
		poly_mapper.UseLookupTableScalarRangeOn()
		poly_mapper.Update()

	# Set Actor
	if lod:
		actor = vtk.vtkLODActor()
		actor.SetNumberOfCloudPoints(lod_points)
		actor.GetProperty().SetPointSize(lod_points_size)
	else:
		actor = vtk.vtkActor()

	actor.SetMapper(poly_mapper)

	actor.GetProperty().SetInterpolationToPhong()
	actor.GetProperty().BackfaceCullingOn()
	actor.GetProperty().SetOpacity(opacity)

	return actor
if __name__ == "__main__":
	main()
