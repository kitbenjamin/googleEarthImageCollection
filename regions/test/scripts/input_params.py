# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:24:15 2019

@author: kitbe
"""
#%%
import yaml
import pyproj
#%%
# get all the required functions
execfile('scripts/functions.py')
#%%
configPath = "metaData/imageCollectionConfig.yml"
with open(configPath) as file:
    meta = yaml.load(file, Loader=yaml.FullLoader)

##create a series of lat, lon values
#latitude sequence: this represents what would be a sequence of coordinates.
#Each coordinate represents the locaiton of an individual "chunk"
#of the surface processed by AgiSoft.
# define variables
collectionArea = meta['regionArea']
#latitiudes
latstart = collectionArea['latStart']
latsize = collectionArea['latSize']
latend = latstart + latsize
latstep = collectionArea['latIntervalSize']
latPoints = UTMseq(latstart, latend, latstep)

#longitudes
lonstart = collectionArea['lonStart']
lonsize = collectionArea['lonSize']
lonend = lonstart + lonsize
lonstep = collectionArea['lonIntervalSize']
lonPoints = UTMseq(lonstart, lonend, lonstep)

latPointsGrid, lonPointsGrid = np.meshgrid(latPoints, lonPoints, indexing = 'xy')

#R location
RscriptLoc = meta['scriptDirectories']['RDir']

#name of the kml - shown inside the kml file
KMLname = meta['projectName']

#within each "chunk", sample all surfaces within the grid cell
#how the surface is sampled is determined by R script rotateCameraAroundChunkOrigin.R.
#the camera circles around the chunk origin
#comma delimited character of camera zenith angles
#each zenith angle represents the zenith angle of a camera rotating 360 degrees around the chunk origin
cameraOptions = meta['cameraOptions']
zenithAngles = cameraOptions['zenithAngles']

#nSamplesAroundOrigin- comma delimited string for each zenith angle, what angular resolution n 
# around the central point i.e. n = 360/nSamplesAroundOrigin
nSamplesAroundOrigin = cameraOptions['nSamplesAroundOrigin']
#camera path length [m] - this is constant for all zenith angles
pathLengths = cameraOptions['pathLengths']
#values that [probably] dont need to change
#Horizontal FOV (degrees) of camera. Vertical FOV is implicitly related to aspect ratio of image
horizFov = cameraOptions['horizFov']
#"range" of camera - I have no idea what this does but if you set to zero and set [altitudeMode]
#to zero then this doesn't do anything
range0 = cameraOptions['range0']
#altitude reference for camera
altitudeMode = cameraOptions['altitudeMode']
#how long to look at each image within each chunk (seconds)?
lookAtDuration = cameraOptions['lookAtDuration']
#define proj
myProjString = meta['projection']
myProj = pyproj.Proj(myProjString)
# google earth directory
GEdir = meta['scriptDirectories']['googleEarthDir']
GEdir = GEdir + 'googleearth.exe'
#time before google earth will timeout
GEtimeout = meta['googleEarthOptions']['GEtimeout']
####end of input parameters####