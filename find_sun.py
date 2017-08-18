import cv2
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import math


def find_sun(im,threshold_value):
	# Input image is a numpy 3D array.
	
	im_RGB = im[:,:,[2,1,0]]
	
	red = im_RGB[:,:,0]
	green = im_RGB[:,:,1]
	blue = im_RGB[:,:,2]
	
	
	all_coord = np.where( red > threshold_value )

	all_coord = np.asarray(all_coord)

	length = np.shape(all_coord)[1]

	sum_x = np.sum(all_coord[0,:])
	sum_y = np.sum(all_coord[1,:])
	

	if (sum_x == 0 or sum_y == 0):
		 centroid_x = np.nan
		 centroid_y = np.nan
	else:
		 
		centroid_x = int(sum_x/length)
		centroid_y = int(sum_y/length)
	
	return(centroid_x,centroid_y)
