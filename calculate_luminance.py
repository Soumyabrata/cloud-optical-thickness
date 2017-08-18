import cv2
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import csv
import datetime
from glob import glob
import os
import exifread


# User defined functions
from nearest import *
from normalize_array import *
from SG_solarmodel import *
from find_sun import *
from cmask import *
from read_COT import *


# Index all the images
global_files = []
#The sky images are not provided here. You need to change this path location accordingly.
start_dir = '/Volumes/shilpa/sky_images/2015/'


# Check for all JPEG images if any.
pattern  = "*.jpg"
for direc,_,_ in os.walk(start_dir):
    global_files.extend(glob(os.path.join(direc,pattern)))

print (len(global_files))



# Reading the COT file
file_path = "./COT_values/2015/COT2015.txt"
YEAR = 2015
(datetime_COT,COT_values)= readingCOT(file_path,YEAR)

# Our experiment site at the rooftop of the university building.
lat = 1.3429943
longitude = 103.6810899

file_name = './average_luminance/2015data.txt'
text_file = open(file_name, "w")

# Header line
text_file.write("Date, TimeImage, TimeMODIS, Luminance, COT, ClearSkyRadiationForTimeImage , ClearSkyLuminanceForTimeImage \n")    


# Parsing the datetime objects of COT
for robin,particular_date in enumerate(datetime_COT):


    YY = particular_date.year
    MM = particular_date.month
    DD = particular_date.day
    HH = particular_date.hour
    MINT = particular_date.minute
    YY = str(YY)
    MM = str(MM)
    DD = str(DD)
    HH = str(HH)
    MINT = str(MINT)
    if len(MM)==1:
        MM = str(0)+MM
    if len(DD)==1:
        DD = str(0)+DD


    my_pattern = YY + '-' + MM + '-' + DD + '-' + HH
    print (my_pattern)

    check_time = datetime.datetime(int(YY),int(MM),int(DD),int(HH),int(MINT),0)

    # Select the possible candidates
    selected_files = []
    for particular_file in global_files:
        if (my_pattern in particular_file) and ('low' not in particular_file) and ('high' not in particular_file):
            selected_files.append(particular_file)


    print ('Total found ',len(selected_files), ' files for comparison')
    
    luminance_array = []
    CSR_array = []
    CSL_array = []
    
    # If there are possble files for comparison
    if len(selected_files)>0:
        print ('COT = ', COT_values[robin])
        
        # Find the different time stamps
        selected_timestamps = []
        for one_file in selected_files:
            f1 = open(one_file, 'rb')
            tags = exifread.process_file(f1)
            date_time = tags["EXIF DateTimeDigitized"].values
            im_date = date_time[0:10]
            im_time = date_time[11:20]

            date_components = im_date.split(":")
            YY = int(date_components[0])
            MM = int(date_components[1])
            DD = int(date_components[2])

            time_components = im_time.split(":")
            HH = int(time_components[0])
            MINT = int(time_components[1])
            SEC = int(time_components[2])

            one_image_time = datetime.datetime(YY,MM,DD,HH,MINT,SEC)
            selected_timestamps.append(one_image_time)
            
            time_gap = np.abs((one_image_time-check_time).total_seconds())
            
            

            # Now select all files within +/- 15 mins
            if abs(time_gap)<900:
                
                print ('within 15 mins---adding')
                # Check the corresponding index to locate the image
                location_index = selected_timestamps.index(one_image_time)

                ClosestImageFile = selected_files[location_index]
                print (ClosestImageFile)

                f1 = open(ClosestImageFile, 'rb')
                tags = exifread.process_file(f1)
                exp_time = tags["EXIF ExposureTime"].values
                exp_time1 = exp_time[0].num / exp_time[0].den

                # Calculate the luminance 
                im1 = cv2.imread(ClosestImageFile)
            
                index = [1728, 2592]  # Center of the image
                im_mask = cmask(index,250,im1) # Mask with radius 1000 pixels
                red = im1[:,:,2]
                green = im1[:,:,1]
                blue = im1[:,:,0]

                red = red.astype(float)
                green = green.astype(float)
                blue = blue.astype(float)

                # RGB images for transfer
                red_image = np.multiply(red,im_mask)
                green_image = np.multiply(green,im_mask)
                blue_image = np.multiply(blue,im_mask)

                im_mask = im_mask.flatten()
                find_loc = np.where(im_mask==1)
                find_loc = list(find_loc)

                red = red.flatten()
                blue = blue.flatten()
                green = green.flatten()

                red_select = red[list(find_loc)]
                green_select = green[list(find_loc)]
                blue_select = blue[list(find_loc)]
    
                lum = 0.2126*blue_select + 0.7152*green_select + 0.0722*red_select
        
                lum = np.mean(lum)
                unityLDRLuminance = lum/exp_time1
                print ('Luminance is ', unityLDRLuminance)
                
                luminance_array.append(unityLDRLuminance)
                
                # Find the clear sky radiation for ImageTime
                date_part = datetime.datetime(YY, MM, DD, HH, MINT, SEC)
                
                CSR = SG_model(date_part)
                CSL = (CSR - 65.24)/0.002246
                
                CSR_array.append(CSR)
                CSL_array.append(CSL)
                
            else:
                print ('outside 15 mins---not adding')
         
        print ('averaging the items ..')        
        luminance_array = np.array(luminance_array)
        CSR_array = np.array(CSR_array)
        CSL_array = np.array(CSL_array)
        
        print (luminance_array)
        print (np.mean(luminance_array))    
            
        text_file.write("%s,%s,%s,%s,%s,%s,%s\n" %(particular_date, one_image_time, check_time, np.mean(luminance_array), COT_values[robin], np.mean(CSR_array), np.mean(CSL_array)))    


text_file.close() 
print ('Computation complete')






