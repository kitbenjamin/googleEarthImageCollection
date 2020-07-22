# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 16:27:52 2019

@author: kitbe
"""

#%%
from __future__ import division
import pandas as pd
import numpy as np
import subprocess
import os
import math
import rasterio
#%%
# execute the functions file
execfile('scripts/functions.py')
# get the input parameters
execfile('scripts/input_params.py')
#%%
#create the height raster usig google maps api 
print('creating height raster')
writeHeightsRast = subprocess.Popen([RscriptLoc + str('Rscript.exe'), '--vanilla', 'scripts/writeASLraster.R'], 
                                     stdout = subprocess.PIPE, stderr = subprocess.PIPE)
writeHeightsRast.wait()
out, err = writeHeightsRast.communicate()
if writeHeightsRast.returncode != 0:
    raise(Exception('Error creating height raster. Process returned code ' + str(writeHeightsRast.returncode) +
                    ' with message: '+ err))
#%%
#import data 
runs = os.listdir('googleEarthOut')
firstRun = runs[0]
imgMeta = pd.read_csv('googleEarthOut/'+firstRun+'/imageIntervalTable_'+firstRun+'.csv')
imgMeta['run'] = firstRun
for i in runs[1:]:
    runDF = pd.read_csv('googleEarthOut/'+i+'/imageIntervalTable_'+i+'.csv')
    runDF['run'] = i
    imgMeta = pd.concat([imgMeta, runDF], axis = 0, ignore_index=True)
#%%
print('Calculating camera view domains')
#%%
imgMeta['zenith'] = imgMeta['zenith'].astype(float)
imgMeta['azimuth'] = imgMeta['azimuth'].astype(float)
#%%
#get the distance from the camera to central point (c)
imgMeta['cDistance'] = camToGround(imgMeta['zenith'], imgMeta['Z'])
#%%
# use azimuth to find the angle 'theta'- the angle measured from the zero x plane to central view direction.
# then convert from a polar coordinate system to a cartesian by using x = x_cam + cDistance*cos(theta)
# and y = y_cam + cDistance*sin(theta). 
imgMeta['theta'] = np.where(imgMeta['azimuth'] > 90, 450 - imgMeta['azimuth'], 90 - imgMeta['azimuth']).astype(float)

imgMeta['centralX'], imgMeta['centralY'] = convToCartesian(imgMeta['X'], imgMeta['Y'], imgMeta['cDistance'], imgMeta['theta'])
imgMeta['central'] = map(list, zip(imgMeta['centralX'], imgMeta['centralY']))

#%%
## define two directions- away from camera (r) and perpendicular to the azimuth of the camera (s)
# find the nearest (r1) and furthest (r2) in points of viewing polygon in away-camera dimension 
imgMeta['r1Distance'] = camToGround((imgMeta['zenith'] - (horizFov/2)), imgMeta['Z'])
imgMeta['r2Distance'] = camToGround((imgMeta['zenith'] + (horizFov/2)), imgMeta['Z'])

imgMeta['r1X'], imgMeta['r1Y'] = convToCartesian(imgMeta['X'], imgMeta['Y'], imgMeta['r1Distance'], imgMeta['theta'])
imgMeta['r2X'], imgMeta['r2Y'] = convToCartesian(imgMeta['X'], imgMeta['Y'], imgMeta['r2Distance'], imgMeta['theta'])
#%%
# get the distances l and L - the vectors from camera to r1 and r2 respectively
imgMeta['l'] = imgMeta['Z'] / np.cos(np.radians(imgMeta['zenith'] - (horizFov/2)))
imgMeta['drY'] = imgMeta['r2Y'] - imgMeta['r1Y']
imgMeta['drX'] = imgMeta['r2X'] - imgMeta['r1X']
imgMeta['dr'] = np.sqrt(imgMeta['drY']**2 + imgMeta['drX']**2)

#to get L use cosine rule
imgMeta['angleL'] = 90 - (horizFov/2) + imgMeta['zenith']
imgMeta['L'] = np.sqrt(imgMeta['l']**2 + imgMeta['dr']**2 - (2*imgMeta['l']*imgMeta['dr']*np.cos(np.radians(imgMeta['angleL']))))
#%%
#method 2- uses trig differently to get L (use to check trig is correct)
# =============================================================================
# imgMeta['L1'] = imgMeta['l'] * np.cos(np.radians(horizFov))
# imgMeta['angleb'] = np.degrees(np.arcsin(imgMeta['Z']/imgMeta['l']))
# angleL1 = 90 - horizFov
# imgMeta['angleL2'] = 180 - angleL1 - imgMeta['angleb']
# imgMeta['Lmethod2'] = imgMeta['L1'] + imgMeta['dr'] * np.sin(np.radians(runNo['angleL2']))
# =============================================================================
#%%
# distance from the points r1 and r2 to the edge of the corners of the polgon 
imgMeta['dS1'] = camToGround(horizFov/2, imgMeta['l'])
imgMeta['dS2'] = camToGround(horizFov/2, imgMeta['L'])
#%%
# calculate new thetas
imgMeta['theta2r'] = imgMeta['theta'] + 270
imgMeta['theta2l'] = imgMeta['theta'] + 90 

#%% 
# get coordinates of the corners of the polygons
imgMeta['r1slX'], imgMeta['r1slY'] = convToCartesian(imgMeta['r1X'], imgMeta['r1Y'], imgMeta['dS1'], imgMeta['theta2l'])
imgMeta['r1sl'] = map(list, zip(imgMeta['r1slX'], imgMeta['r1slY']))

imgMeta['r2slX'], imgMeta['r2slY'] = convToCartesian(imgMeta['r2X'], imgMeta['r2Y'], imgMeta['dS2'], imgMeta['theta2l'])
imgMeta['r2sl'] = map(list,zip(imgMeta['r2slX'], imgMeta['r2slY']))

imgMeta['r1srX'], imgMeta['r1srY'] = convToCartesian(imgMeta['r1X'], imgMeta['r1Y'], imgMeta['dS1'], imgMeta['theta2r'])
imgMeta['r1sr'] = map(list, zip(imgMeta['r1srX'], imgMeta['r1srY']))

imgMeta['r2srX'], imgMeta['r2srY'] = convToCartesian(imgMeta['r2X'], imgMeta['r2Y'], imgMeta['dS2'], imgMeta['theta2r'])
imgMeta['r2sr'] = map(list, zip(imgMeta['r2srX'], imgMeta['r2srY']))


#%%
# for qgis img
# =============================================================================
# pointLocs = pd.DataFrame(columns = ['elevation', 'x', 'y', 'type'])
# for i, row in imgMeta.iterrows():
#     pointLocs = pointLocs.append({'elevation' : row['elev'], 'x' : row['X'], 'y' : row['Y'], 'type' : 'camera_position'}, ignore_index = True)  
#     pointLocs = pointLocs.append({'elevation' : row['elev'], 'x' : row['centralX'], 'y' : row['centralY'], 'type': 'central'}, ignore_index = True)  
#     pointLocs = pointLocs.append({'elevation' : row['elev'], 'x' : row['r1slX'], 'y' : row['r1slY'], 'type': 'bottom_left'}, ignore_index = True)  
#     pointLocs = pointLocs.append({'elevation' : row['elev'], 'x' : row['r2slX'], 'y' : row['r2slY'], 'type': 'top_left'}, ignore_index = True)  
#     pointLocs = pointLocs.append({'elevation' : row['elev'], 'x' : row['r1srX'], 'y' : row['r1srY'], 'type': 'bottom_right'}, ignore_index = True)  
#     pointLocs = pointLocs.append({'elevation' : row['elev'], 'x' : row['r2srX'], 'y' : row['r2srY'], 'type': 'top_right'}, ignore_index = True)  
# =============================================================================
#%%
#drop unneeded columns
imgMeta.columns
imgMeta = imgMeta.drop([u'cDistance', u'theta', u'r1Distance', u'r2Distance', u'r1X', u'r2X', u'r1Y',
                   u'r2Y', u'l', u'drY', u'drX', u'dr', u'angleL', u'L', u'dS1', u'dS2',
                   u'theta2r', u'theta2l', 'centralX', 'centralY', 'r1slX', 'r1slY', 'r2slX', 'r2slY', 
                   'r1srX', 'r1srY', 'r2srX', 'r2srY'], axis = 1)
#%%
#read in heights raster
gmHeightsPath = os.path.join('metaData', 'GM_heights.tif')
if os.path.exists(gmHeightsPath):
    gmHeights = rasterio.open(os.path.join('metaData', 'GM_heights.tif'))
else:
    raise(Exception('GM_heights.tif has not been created'))
#get the height band
heightBand = gmHeights.read(1)
#%%
print('extracting all height values from raster')
for i in ['central', 'r1sl', 'r2sl', 'r1sr', 'r2sr']:
    imgMeta[i+'_elev'] = imgMeta[i].apply(lambda x: getRasterPointHeight(x, gmHeights, heightBand))
#%%
print('Adjusting view domain point positions based on elevation')
# create a plane using two nearest point- find intersection between line from camera to point
# and plane to adjust point for height
imgMeta.insert(len(imgMeta.columns), 'r1sl_adjusted', 'None')
imgMeta.insert(len(imgMeta.columns), 'r1sr_adjusted', 'None')
imgMeta.insert(len(imgMeta.columns), 'r2sl_adjusted', 'None')
imgMeta.insert(len(imgMeta.columns), 'r2sr_adjusted', 'None')
imgMeta.insert(len(imgMeta.columns), 'zDif_r1sl_r2sr', 'None')
imgMeta.insert(len(imgMeta.columns), 'zDif_r1sr_r2sl', 'None')

for i, r in imgMeta.iterrows():
    #ensure all as arrays
    pointA = np.array(np.append(r['r1sl'], r['r1sl_elev'])).astype(float)
    pointB = np.array(np.append(r['r1sr'], r['r1sr_elev'])).astype(float)
    pointC = np.array(np.append(r['r2sl'],  r['r2sl_elev'])).astype(float)
    pointD = np.array(np.append(r['r2sr'], r['r2sr_elev'])).astype(float)
    central = np.array(np.append(r['central'], r['central_elev'])).astype(float)
    cam = np.array([r['X'], r['Y'], r['Z']]).astype(float)
    # get the difference between predicted and real height of central point- to decide whether to flag for 
    # non-uniform topography
    # r1sl, r2sr and r1sr, r2sl (opposites) will wield the same heights as their planes intersect at central point
    zDif_r1sl_r2sr = compCentZ(pointA, pointB, pointC, central)
    zDif_r1sr_r2sl = compCentZ(pointB, pointA, pointD, central)
    # get the points adjusted for height
    r1sl_adj = getPlaneAdjPoint(pointA, pointB, pointC, cam)
    r1sr_adj = getPlaneAdjPoint(pointB, pointA, pointD, cam)
    r2sl_adj = getPlaneAdjPoint(pointC, pointD, pointA, cam)
    r2sr_adj = getPlaneAdjPoint(pointD, pointB, pointC, cam)

    imgMeta.at[i, 'r1sl_adjusted'] = r1sl_adj
    imgMeta.at[i,'r1sr_adjusted'] = r1sr_adj
    imgMeta.at[i,'r2sl_adjusted'] = r2sl_adj
    imgMeta.at[i,'r2sr_adjusted'] = r2sr_adj
    imgMeta.at[i,'zDif_r1sl_r2sr'] = zDif_r1sl_r2sr
    imgMeta.at[i,'zDif_r1sr_r2sl'] = zDif_r1sr_r2sl
    
#%%
print('Creating view domain KML files')
# create view domains folder
for i in runs:
    if os.path.exists('kmlFiles/viewDomains/'+i) == False:
        os.makedirs('kmlFiles/viewDomains/'+i)
#%%
# get the latitude and longitude of each point
pointCols = ['central', 'r1sl', 'r2sl', 'r1sr', 'r2sr', 'r1sl_adjusted',
             'r2sl_adjusted', 'r1sr_adjusted', 'r2sr_adjusted']
for i in pointCols:
    imgMeta[i+'_latlon'] = imgMeta[i].apply(lambda x: convToLonlat(x, myProj))
#%%
#create kml files showing swath of each image
imgMetaGroup = imgMeta.groupby('run')
for name, data in imgMetaGroup:
    createKML(data, name, adjusted = True)
    createKML(data, name, adjusted = False)
#%%
# add elevation into point list
for i, row in imgMeta.iterrows():
    row['central'].append(float(row['central_elev']))
    row['r1sl'].append(float(row['r1sl_elev']))
    row['r1sr'].append(float(row['r1sr_elev']))
    row['r2sl'].append(float(row['r2sl_elev']))
    row['r2sr'].append(float(row['r2sr_elev']))
#%%
conditions = [(np.array(abs(imgMeta.zDif_r1sl_r2sr) > 15) &  np.array(abs(imgMeta.zDif_r1sr_r2sl > 15)))]
outputs = [1]
# if height dif of > 15m between theoretical and real central point 
imgMeta['topography_flag'] = np.select(conditions, outputs)
#%%
#drop unneeded columns
imgMeta = imgMeta.drop([u'central_elev', u'r1sl_elev', u'r2sl_elev', u'r1sr_elev', u'r2sr_elev', u'central_latlon', 
                        u'r1sl_latlon', u'r2sl_latlon', u'r1sr_latlon', u'r2sr_latlon',
                        u'r2sl_adjusted_latlon', u'r1sr_adjusted_latlon', u'r2sr_adjusted_latlon', 
                        u'r1sl_adjusted_latlon', u'zDif_r1sl_r2sr', u'zDif_r1sr_r2sl'], axis = 1)
# 
#%%
# write to a csv 
imgMeta.to_csv('imageInterval/imageViewDomains.csv')
#%%
print('Process complete')
