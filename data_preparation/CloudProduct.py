#!/usr/bin/env ipython3
import gdal
import numpy as np
from utility import *

class CloudProduct:
    def __init__(self, filename, roi_lat = 1.342966, roi_long = 103.680594, roi_width_km = 100):
        self.filename = filename
        try:
            self.data_set = gdal.Open(filename)
            self.center = [roi_lat, roi_long]
            
            self.size5k = None
            self.georef_grid1k = None
        
            # Extract the georeferencing
            sub_lat_set = gdal.Open([sd for sd, descr in self.data_set.GetSubDatasets() if descr.endswith('Latitude (32-bit floating-point)')][0])
            sub_long_set = gdal.Open([sd for sd, descr in self.data_set.GetSubDatasets() if descr.endswith('Longitude (32-bit floating-point)')][0])
            self.georef_grid = np.dstack((sub_lat_set.ReadAsArray(), sub_long_set.ReadAsArray()))
            sub_lat_set = None
            sub_long_set = None
            self.size5k = []
            self.size1k = []
            
            # Definition of the roi to strip the data
            self.lrcrnX = 0          # Lower Right corner
            self.lrcrnY = 0
            self.ulcrnX = 0          # Upper Left corner
            self.ulcrnY = 0 
            self.geoSubSample(roi_lat, roi_long, roi_width_km)

        except:
            print("Error when reading file. Either file does not exist, or is not a valid MOD06 product")
            raise
        
    def geoSubSample(self, center_lat, center_long, width_km):
        assert width_km % 10 == 0, "The size of the roi must be a multiple of 10"
        
        center = np.array([center_lat, center_long])
        grid_center = closest_point(self.georef_grid, center)
        
        
        self.georef_grid = self.georef_grid[grid_center[0] - width_km/10 : grid_center[0] + width_km/10 + 1, \
                                            grid_center[1] - width_km/10 : grid_center[1] + width_km/10 + 1, :]
        grid_center = np.multiply(grid_center, 5)   # Coordinates to center the 1k dataset

        self.ulcrnX = grid_center[0] - width_km/2
        self.ulcrnY = grid_center[1] - width_km/2
        self.lrcrnX = grid_center[0] + width_km/2 + 1
        self.lrcrnY = grid_center[1] + width_km/2 + 1

        # Update size
        self.size5k = [self.georef_grid.shape[0], self.georef_grid.shape[1]]
        self.size1k = [width_km+1, width_km+1]
        # Update derived products
        self.__interpolateGeoreferencing()    
        
    def extractCloudTopHeight_1k(self):
        """Cloud Top height in meters"""
        return self.extractByName('cloud_top_height_1km mod06 (16-bit integer)')
    
    def extractCloudWaterPath_1k(self):
        """ Between all the the cloud water path dataset, return the "Column Water Path two-band retrieval 
            using band 7 and either band 1, 2, or 5 (specified in Quality_Assurance_1km)from best points: not 
            failed in any way, not marked for clear sky restoral."
            In g/m^2.
        """
        return self.extractByName('Cloud_Water_Path (16-bit integer)')
    
    def extractCloudEffectiveRadius_1k(self):
        """ Between all the cloud effective radius dataset, return "Cloud Particle Effective 
            Radius two-channel retrieval using band 7 and either band 1, 2, or 5 (specified in 
            Quality_Assurance_1km)from best points: not failed in any way, not marked for clear 
            sky restoral".
            In micron
        """
        scale_factor = 0.009999999776482582
        return np.multiply(self.extractByName('Cloud_Effective_Radius mod06 (16-bit integer)'), scale_factor)
    
    
    def extractCloudTopTemperature_1k(self):
        """ Cloud Top Temperature in Kelvin. From modis_atmos FAQ:
            Geophysical_Float_Value = scale_factor * (Stored_Integer - add_offset)
            The fill value of -999 becomes 140.009996871
        """
        raw_data = self.extractByName('cloud_top_temperature_1km mod06 (16-bit integer)')
        scale_factor = 0.009999999776482582
        add_offset = -15000
        return np.multiply(np.subtract(raw_data, add_offset), scale_factor)
    
    def extractCloudOpticalThickness_1k(self):
        """ Cloud Optical Thickness. Cloud Optical Thickness two-channel retrieval using band 7 and either 
            band 1, 2, or 5 (specified in Quality_Assurance_1km)from best points: not failed in any way, not 
            marked for clear sky restoral. In percent.
            0% = transparent cloud, 100% : can't see through.
        """
        raw_data = self.extractByName('Cloud_Optical_Thickness mod06 (16-bit integer)')
        scale_factor = 0.009999999776482582
        return np.multiply(raw_data, scale_factor)
    
    def extractCloudTopPressure_1k(self):
        """Cloud Top height in hPa"""
        scale_factor = 0.1000000014901161
        return np.multiply(self.extractByName('cloud_top_pressure_1km (16-bit integer)'), scale_factor)
    
    def extractCloudPhaseInfrared_1k(self):
        """ Cloud Phase: 
                        0 -- cloud free
                        1 -- water cloud
                        2 -- ice cloud
                        3 -- mixed phase cloud
                        6 -- undetermined phase
        """
        return self.extractByName('Cloud_Phase_Infrared_1km (8-bit integer)')
    
    def extractByName(self, description):
        try:
            sub_ds = gdal.Open([sd for sd, descr in self.data_set.GetSubDatasets() if descr.endswith(description)][0])
            return sub_ds.ReadAsArray()[self.ulcrnX:self.lrcrnX, self.ulcrnY:self.lrcrnY]
        except:
            print("Error while extracting product. Either file sub dataset does not exist,\
 or is not a valid MOD06 product")
            raise
    
    def __interpolateGeoreferencing(self):
        """ Interpolate the georeferencing 5k grid included in the product for 1k and 250m array. This has not
            be test in regard of MOD03 9? (contains 1k grid by NASA) but consistenty of result has been assessed.
            IMP: For this function to work correctly, the roi must contains at least more than 3 element,
            so we can safely interpolate a second dregree spline. 
        """
        latitude = np.dsplit(self.georef_grid, 2)[0]
        longitude = np.dsplit(self.georef_grid, 2)[1]
        from scipy import interpolate
        ## 1k interpolation
        # Indices for the 1k grid
        x = np.arange(latitude.shape[0])
        y = np.arange(latitude.shape[1])
        xx = np.linspace(x.min(), x.max(), self.size1k[0])
        yy = np.linspace(y.min(), y.max(), self.size1k[1])
        # Create the 1k grid : Latitude and longitude
        lat_1k = interpolate.RectBivariateSpline(x, y, latitude)(xx, yy)
        long_1k = interpolate.RectBivariateSpline(x, y, longitude)(xx, yy)
        # Merge
        self.georef_grid1k = np.dstack((lat_1k, long_1k))
        
        
    def dispayOnMap(self, product):
        """ Template function for displaying on a map. Not meant to be used as it is. Present
            a reference layout """
        import matplotlib.pyplot as plt
        import matplotlib.image as mpimg
        from matplotlib import colors
        from mpl_toolkits.basemap import Basemap
        import matplotlib as mpl
        
        fig, ax = plt.subplots()
        fig.set_facecolor('white')
        mpl.rc('font', family='sans-serif') 
        mpl.rc('font', serif='Oxygen-Sans')
        mpl.rc('text', usetex='false') 
        mpl.rcParams.update({'font.size': 11})

        # Basemap ('lcc' = lambert conformal conic).
        map = Basemap(projection = 'lcc', resolution='h', area_thresh=0.1,
            llcrnrlon=103, llcrnrlat=1,                     # A bit bigger area
            urcrnrlon=105, urcrnrlat=2,
            #llcrnrlon=103.529044, llcrnrlat=1.132124,      # Bounding box
            #urcrnrlon=104.160634, urcrnrlat=1.546439,
            lat_0 = 1.342966, lon_0 = 103.680594
            )
        ## Appearance
        map.drawcoastlines()
        #map.bluemarble()
        cmap = mpl.cm.YlOrRd
        cmap.set_bad('k', 1.0)      # Masked value are black
        
        if (product == 'CTH'):
            cth = self.extractCloudTopHeight_1k()
            ax.set_title('.'.join(self.filename.split('/')[-1].split('.')[0:-2]) + ' \n Cloud Top Height (m)')
            cax = map.pcolormesh(self.georef_grid1k[:, :, 1],
                                 self.georef_grid1k[:, :, 0],
                                 np.ma.masked_where(cth <= 0, cth),      # Common sense
                                 shading='flat',cmap=cmap, latlon=True)
            cbar = fig.colorbar(cax)
        elif (product == 'CTT'):
            ctt = self.extractCloudTopTemperature_1k()
            ax.set_title('.'.join(self.filename.split('/')[-1].split('.')[0:-2]) + ' \n Cloud Top Temperature (K)')
            cax = map.pcolormesh(self.georef_grid1k[:, :, 1],
                                 self.georef_grid1k[:, :, 0],
                                 np.ma.masked_where(ctt <= 141, ctt),
                                 shading='flat',cmap=cmap, latlon=True)
            cbar = fig.colorbar(cax)
        elif (product == 'CTP'):
            ctp = self.extractCloudTopPressure_1k()
            ax.set_title('.'.join(self.filename.split('/')[-1].split('.')[0:-2]) + ' \n Cloud Top Pressure (hPa)')
            cax = map.pcolormesh(self.georef_grid1k[:, :, 1],
                                 self.georef_grid1k[:, :, 0],
                                 np.ma.masked_where(ctp <= 0, ctp),
                                 shading='flat',cmap=cmap , latlon=True)
            cbar = fig.colorbar(cax)
        elif (product == 'CWP'):
            cwp = self.extractCloudWaterPath_1k()
            ax.set_title('.'.join(self.filename.split('/')[-1].split('.')[0:-2]) + ' \n Cloud Water Path (g/m^2)')
            cax = map.pcolormesh(self.georef_grid1k[:, :, 1],
                                 self.georef_grid1k[:, :, 0],
                                 np.ma.masked_where(cwp <= 0, cwp),      # Common sense
                                 shading='flat',cmap=cmap , latlon=True)
            cbar = fig.colorbar(cax)
        elif (product == 'COT'):
            cot = self.extractCloudOpticalThickness_1k()
            ax.set_title('.'.join(self.filename.split('/')[-1].split('.')[0:-2]) + ' \n Cloud Optical Thickness (%)')
            cax = map.pcolormesh(self.georef_grid1k[:, :, 1],
                                 self.georef_grid1k[:, :, 0],
                                 np.ma.masked_where(cot <= 0, cot),
                                 shading='flat',cmap=cmap , latlon=True)
            cbar = fig.colorbar(cax)
        elif (product == 'CER'):
            cer = self.extractCloudEffectiveRadius_1k()
            ax.set_title('.'.join(self.filename.split('/')[-1].split('.')[0:-2]) + ' \n Cloud Effective Radius (micron)')
            cax = map.pcolormesh(self.georef_grid1k[:, :, 1],
                                 self.georef_grid1k[:, :, 0],
                                 np.ma.masked_where(cer <= 0, cer),      # Common sense
                                 shading='flat',cmap=cmap , latlon=True)
            cbar = fig.colorbar(cax)
        elif (product == 'CPI'):
            ax.set_title('.'.join(self.filename.split('/')[-1].split('.')[0:-2]) + ' \n Cloud Phase')
            cmap = colors.ListedColormap(['black', 'blue', 'white', 'lightskyblue', 'red'])
            bounds = [0, 0.5, 1.5, 2.5, 3.5, 5]
            norm = colors.BoundaryNorm(bounds, cmap.N)
            cax = map.pcolormesh(self.georef_grid1k[:, :, 1],
                                 self.georef_grid1k[:, :, 0],
                                 self.extractCloudPhaseInfrared_1k(),
                                 shading='flat', cmap=cmap, norm=norm, latlon=True)
            cbar = fig.colorbar(cax, ticks=[0, 1, 2, 3, 5])
            cbar.ax.set_yticklabels(['Cloud Free', 'Water Cloud', 'Ice Cloud', 'Mixed Phase Cloud', 'Undetermined'])
        
        # Point for WSI position
        map.scatter(self.center[1], self.center[0], s=100, facecolor='none', edgecolors='g', latlon = True, alpha=1)
        fig.tight_layout()
        plt.show()
        
