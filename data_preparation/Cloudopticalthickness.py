# -*- coding: utf-8 -*-
"""
Created on Tue Mar 31 19:32:03 2015

@author: YUAN0053
"""

#!/usr/bin/env ipython3

import glob
from utility import *
from CloudProduct import CloudProduct

products = ['06']
satellites = ['MYD']
extension = '.hdf'

location = [1.34213, 103.6805]#NTU [1.34047, 103.88819]Taiseng
roi_size = 50

sel = 3 # Save a 3-by-3 box around the selected point

#mask_path = 'data/data-*' 
mask_path = 'Raw data 2014/data-2014-1-*' 
days = []
x = []
y = []
z = []
for day in glob.glob(mask_path):
    for satellite in satellites:
        s1 = day + '/' + satellite
        for product in products:
            s2 = s1 + product + '*' + extension
            for files in glob.glob(s2):
                try:
                    print('Processing File: ', files)
                    seed = '-'.join(files.split('.')[1:3])
                    cloudproduct = CloudProduct(files, location[0], location[1], roi_size)
                    georef = cloudproduct.georef_grid1k
                    #topheight = cloudproduct.extractCloudTopHeight_1k()
                    opticalthickness = cloudproduct.extractCloudOpticalThickness_1k()
                    #phase=cloudproduct.extractCloudPhaseInfrared_1k()
                    #radius = cloudproduct.extractCloudEffectiveRadius_1k()
                    #Liquidwaterpath = cloudproduct.extractCloudWaterPath_1k()
                    
                    grid_location = closest_point(georef, location)
                    # Subsample data
                    #topheight = topheight[grid_location[0]-sel//2 : grid_location[0]+sel//2+1 ,
                    #            grid_location[1]-sel//2 : grid_location[1]+sel//2+1 ]
                    
                    #phase = phase[grid_location[0]-sel//2 : grid_location[0]+sel//2+1 ,
                    #             grid_location[1]-sel//2 : grid_location[1]+sel//2+1 ]
                    opticalthickness = opticalthickness[grid_location[0]-sel//2 : grid_location[0]+sel//2+1 ,
                                 grid_location[1]-sel//2 : grid_location[1]+sel//2+1 ]     
                    #radius = radius[grid_location[0]-sel//2 : grid_location[0]+sel//2+1 ,
                                #grid_location[1]-sel//2 : grid_location[1]+sel//2+1 ]    
                    #Liquidwaterpath = Liquidwaterpath[grid_location[0]-sel//2 : grid_location[0]+sel//2+1 ,
                                #grid_location[1]-sel//2 : grid_location[1]+sel//2+1 ]            
                    #baseheight = topheight - opticalthickness
                    #LWP = 4*opticalthickness*radius/6
                    
                    #georef = georef[grid_location[0]-sel//2 : grid_location[0]+sel//2+1 
                                    #grid_location[1]-sel//2 : grid_location[1]+sel//2+1, : ]
                    #data = np.reshape(data,(1,9))
                    #print(topheight)
                    #print(opticalthickness)
                    ##print(phase)
                    print(opticalthickness)
                    #print(baseheight)
                    #print(LWP)
                    #print(Liquidwaterpath)
                except:
                    print('ERROR:', files)
                else:
                    #x.append(phase)
                    y.append(opticalthickness)
                    #z.append(Liquidwaterpath)
                    #LWP.append(Liquidwaterpath)
#                    save_as_mat('georef-' + seed, georef)
#                    save_as_mat('data-' + seed, data)
                    
#save_as_mat('phase',x)
save_as_mat('opticalthickness',y)

#save_as_mat('LWP',Liquidwaterpath)
               
