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
import pyproj
import os
import math
from pykml.factory import KML_ElementMaker as KML
from pykml.factory import GX_ElementMaker as GX
from lxml import etree
import yaml
#%%
# calculate distance from a camera to a point on the ground given the angle of the camera 
def camToGround(angles, heights):
    return np.tan(np.radians(angles)) * heights
#%%
# uses the distance from the camera and its angle to calculate the x, y (easting, northing) of the point
def convToCartesian(x, y, cDistance, theta):
    return x + cDistance*np.cos(np.radians(theta)),  y + cDistance*np.sin(np.radians(theta))
#%%
def conv_lonlat(df, series, index, pointString):
    df.at[index, pointString +'_lat'] = myProj(series[pointString][0], series[pointString][1], inverse = True)[1]
    df.at[index, pointString +'_lon'] = myProj(series[pointString][0], series[pointString][1], inverse = True)[0]
#%%
#method from: http://geomalgorithms.com/a05-_intersect-1.html
#cheers: https://gist.github.com/TimSC/8c25ca941d614bf48ebba6b473747d72
def getPlaneAdjPoint(point1, point2, point3, camera):
    # get the normal to the plane of the three points (n)
    plane_normal =  np.cross(np.subtract(point1, point2), np.subtract(point1, point3))
    #get the point1 (where height assumed to be zero)
    currentPoint1 = np.append(point1[:-1],0) 
    #vector of the line from camera to point1 (u)
    camTo1 = currentPoint1 - camera 
    # vector from the point on the plane to point on the line (w)
    planeToLine = currentPoint1 - point1
    #dot product of plane normal and intersecting line (n.u)
    planeNormDotLine = plane_normal.dot(camTo1)
    # point along the vector (si = n.w/n.u)
    si = -plane_normal.dot(planeToLine) / planeNormDotLine
    # work out coordinates of point (w + si*u + planepoint)
    adjPoint = (planeToLine + (si * camTo1)) + point1
    return list(adjPoint)
#%%
# maths based from http://tutorial.math.lamar.edu/Classes/CalcIII/EqnsOfPlanes.aspx
# find the 'theoretical' height of the central point i.e the height if the topography was 
# perfectly planar
def compCentZ(point1, point2, point3, central):
    # calculate the normal    
    plane_normal =  np.cross(np.subtract(point1, point2), np.subtract(point1, point3))
    # get the coefficients for the plane equation
    # ax +by +cz = d
    a = plane_normal[0]
    b = plane_normal[1]
    c = plane_normal[2]
    d = a*point1[0] + b*point1[1] + c*point1[2]
    # rearrange for z and plut in central x and y coordinates
    # z = (d -ax -by)/c
    zCentralPlane = (d- a*central[0] - b*central[1])/c
    # difference between real centre height and that predicted by plane
    centralZdif = central[2] - zCentralPlane
    return centralZdif
#%%
# create a kml file showing polygon of viewing points
def createKML(df, run, adjusted):
    for i, row in df.iterrows():
        if adjusted == True:
            lon1, lat1 = myProj(row['r1sl_adjusted'][0], row['r1sl_adjusted'][1], inverse = True)
            lon2, lat2 = myProj(row['r1sr_adjusted'][0], row['r1sr_adjusted'][1], inverse = True)
            lon3, lat3 = myProj(row['r2sl_adjusted'][0], row['r2sl_adjusted'][1], inverse = True)
            lon4, lat4 = myProj(row['r2sr_adjusted'][0], row['r2sr_adjusted'][1], inverse = True)
            
            coordinates =   (str(lon1)+','+str(lat1)+','+ str(row['r1sl_adjusted'][2] + 5) +' '+
                            str(lon3)+','+str(lat3)+','+ str(row['r2sl_adjusted'][2] + 5) +' '+
                            str(lon4)+','+str(lat4)+','+ str(row['r2sr_adjusted'][2] + 5 ) +' '+
                            str(lon2)+','+str(lat2)+','+ str(row['r1sr_adjusted'][2] + 5))
            color = '#a00000ff'
        else:
            lon1 = row['r1sl_lon']
            lat1 = row['r1sl_lat']
            lon2 = row['r1sr_lon']
            lat2 = row['r1sr_lat']
            lon3 = row['r2sl_lon']
            lat3 = row['r2sl_lat']
            lon4 = row['r2sr_lon']
            lat4 = row['r2sr_lat']
            
            coordinates =   (str(lon1)+','+str(lat1)+','+ str(float(row['r1sl_elev']) + 5) +' '+
                            str(lon3)+','+str(lat3)+','+ str(float(row['r2sl_elev']) + 5) +' '+
                            str(lon4)+','+str(lat4)+','+ str(float(row['r2sr_elev']) + 5 ) +' '+
                            str(lon2)+','+str(lat2)+','+ str(float(row['r1sr_elev']) + 5))
            color = '#a0ff0000'
            
        polygon_kml = KML.kml( 
                    KML.Placemark(
                        KML.Style(
                        KML.PolyStyle(
                                KML.color(color)
                                )
                        ),         
                        KML.name(str(run)+'_'+str(row['Label'])),
                        KML.Polygon(
                           KML.extrude(1), 
                           GX.altitudeMode('absolute'),
                           KML.outerBoundaryIs(
                                   KML.LinearRing(
                                           KML.coordinates(
                                            coordinates
                                            )
                                    )
                            )
                     )
                  )
                )
        
        if adjusted == True:
            outfile = open('out/viewDomains/'+str(run)+'/'+str(row['Label'])+'_adj.kml', 'w')
        else: 
            outfile = open('out/viewDomains/'+str(run)+'/'+str(row['Label'])+'.kml', 'w')
        outfile.write(etree.tostring(polygon_kml, pretty_print = True)) 
        outfile.close()
#%%
def assertSameCoords(dataframe, elevations, index, noDP):
    assert abs(float(elevations[index][0]) - round(dataframe.loc[index, 'central_lat'], noDP[0])) < 10**noDP[0] and abs(float(elevations[index][1]) - round(dataframe.loc[index, 'central_lon'], noDP[1])) < 10**noDP[1]
    assert abs(float(elevations[index][3]) - round(dataframe.loc[index, 'r1sl_lat'], noDP[2])) < 10**noDP[2] and abs(float(elevations[index][4]) - round(dataframe.loc[index, 'r1sl_lon'], noDP[3])) < 10**noDP[3]
    assert abs(float(elevations[index][6]) - round(dataframe.loc[index, 'r2sl_lat'], noDP[4])) < 10**noDP[4] and abs(float(elevations[index][7]) - round(dataframe.loc[index, 'r2sl_lon'], noDP[5])) < 10**noDP[5]
    assert abs(float(elevations[index][9]) - round(dataframe.loc[index, 'r1sr_lat'], noDP[6])) < 10**noDP[6] and abs(float(elevations[index][10]) - round(dataframe.loc[index, 'r1sr_lon'], noDP[7])) < 10**noDP[7]
    assert abs(float(elevations[index][12]) - round(dataframe.loc[index, 'r2sr_lat'], noDP[8])) < 10**noDP[8] and abs(float(elevations[index][13]) - round(dataframe.loc[index, 'r2sr_lon'], noDP[9])) < 10**noDP[9]

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
# read in configuration file
configPath = "metaData/imageCollectionConfig.yml"
with open(configPath) as file:
    meta = yaml.load(file, Loader=yaml.FullLoader)
#get horizontal field of view
horizFov = meta['cameraOptions']['horizFov']
#get location of R on users computer
RscriptLoc = meta['scriptDirectories']['RDir']
# get cooridinate system
myProjString = meta['projection']
myProj = pyproj.Proj(myProjString)
#%%
print('Calculating camera view domains')
#%%
#get the distance from the camera to central point (c)
imgMeta['cDistance'] = camToGround(imgMeta['zenith'], imgMeta['Z'])
#%%
# use azimuth to find the angle 'theta'- the angle measured from the zero x plane to central view direction.
# then convert from a polar coordinate system to a cartesian by using x = x_cam + cDistance*cos(theta)
# and y = y_cam + cDistance*sin(theta). 
imgMeta['theta'] = np.where(imgMeta['azimuth'] > 90, 450 - imgMeta['azimuth'], 90 - imgMeta['azimuth'])

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
# get the latitude and longitude of each point
imgMeta2 = imgMeta.iloc[:]
for i, row in imgMeta2.iterrows():
    conv_lonlat(imgMeta2, row, i, 'central')
    conv_lonlat(imgMeta2, row, i, 'r1sl')
    conv_lonlat(imgMeta2, row, i, 'r2sl')
    conv_lonlat(imgMeta2, row, i, 'r1sr')
    conv_lonlat(imgMeta2, row, i, 'r2sr')
#%%
# get only lats lons to use as args for R script
latlons = imgMeta2.loc[:,'central_lat':'r2sr_lon'].values
latlons = [str(item) for sublist in latlons for item in sublist]
#%%
print('Getting elevations from gooogle API: ' + str(int(len(latlons)/2))+' coordinates to process')
# the original command to call r script
popenCMD = [RscriptLoc + str('Rscript.exe'), '--vanilla', '--no-save', 'scripts/getPointHeight.R']
# 408 is approximately the maximum number of args that can be input to the r script 
nIts = int(math.ceil(len(latlons)/408))
# call r script to get heights of each point- must be looped in chunks of less that 408 
output = ''
for i in range(nIts):
    if (len(latlons) - ((i+1)*408)) > 0:
        popenCMDwArgs = popenCMD + latlons[(i)*408:((i + 1) * 408)] + [str(i)]
        coRetrieved = str(((i+1)*408)/2)
    else:
        popenCMDwArgs = popenCMD + latlons[(i)*408:] + [str(i)]
        coRetrieved = str(int(len(latlons)/2))

        
    getHeights = subprocess.Popen(popenCMDwArgs, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    out, err = getHeights.communicate()
    output = output + out
    print(coRetrieved + ' coordinate elevations retrieved')

#%%
# decode 
outsplit = output.decode('ascii').splitlines()
elevations = pd.DataFrame(columns = ['central_elev', 'r1sl_elev', 'r2sl_elev', 'r1sr_elev', 
                                     'r2sr_elev'])

#extract just the elevations
n = 0
elevs = []
for i in range(int(len(outsplit)/4)):
    #namesplit = outsplit[n].replace('$', '').split('_')
    #point = namesplit[0] +'_elev'
    #index = int(namesplit[1])
    
    elev = outsplit[n+2].split()
    elevs.append(elev)
    #elevations.at[index, point] = float(elev)    
    n += 4
#%%
elevs = np.array(elevs)
elevs.shape = (int(len(elevs)/5), 15)
coordIdx = [0,1,3,4,6,7,9,10,12,13]
elevIdx = [2,5,8,11,14]
elevations = []
for i in range(len(elevs)):
    noDP = []
    for n in elevs[i][coordIdx]:
        try:
           noDP.append(len(n.split('.')[1]))
        except:
           noDP.append(0)
    assertSameCoords(imgMeta2, elevs, i, noDP)
    elevations.append(elevs[i][elevIdx])
elevations_DF = pd.DataFrame(elevations, columns = ['central_elev', 'r1sl_elev', 'r2sl_elev', 'r1sr_elev', 'r2sr_elev'])

#%%
# add elevation to other data
imgMeta3 = pd.concat([imgMeta2, elevations_DF], axis = 1)
#%%
print('Adjusting view domain point positions based on elevation')
# create a plane using two nearest point- find intersection between line from camera to point
# and plane to adjust point for height
imgMeta3.insert(len(imgMeta3.columns), 'r1sl_adjusted', 'None')
imgMeta3.insert(len(imgMeta3.columns), 'r1sr_adjusted', 'None')
imgMeta3.insert(len(imgMeta3.columns), 'r2sl_adjusted', 'None')
imgMeta3.insert(len(imgMeta3.columns), 'r2sr_adjusted', 'None')
imgMeta3.insert(len(imgMeta3.columns), 'zDif_r1sl_r2sr', 'None')
imgMeta3.insert(len(imgMeta3.columns), 'zDif_r1sr_r2sl', 'None')

for i, r in imgMeta3.iterrows():
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

    imgMeta3.at[i, 'r1sl_adjusted'] = r1sl_adj
    imgMeta3.at[i,'r1sr_adjusted'] = r1sr_adj
    imgMeta3.at[i,'r2sl_adjusted'] = r2sl_adj
    imgMeta3.at[i,'r2sr_adjusted'] = r2sr_adj
    imgMeta3.at[i,'zDif_r1sl_r2sr'] = zDif_r1sl_r2sr
    imgMeta3.at[i,'zDif_r1sr_r2sl'] = zDif_r1sr_r2sl
    
#%%
print('Creating view domain KML files')
# create view domains folder
for i in runs:
    if os.path.exists('out/viewDomains/'+i) == False:
        os.makedirs('out/viewDomains/'+i)
#%%
#create kml files showing swath of each image
imgMeta3Group = imgMeta3.groupby('run')
for name, data in imgMeta3Group:
    createKML(data, name, adjusted = True)
    createKML(data, name, adjusted = False)

    
#%%
# add elevation into point list
for i, row in imgMeta3.iterrows():
    row['central'].append(float(row['central_elev']))
    row['r1sl'].append(float(row['r1sl_elev']))
    row['r1sr'].append(float(row['r1sr_elev']))
    row['r2sl'].append(float(row['r2sl_elev']))
    row['r2sr'].append(float(row['r2sr_elev']))
#%%
conditions = [(np.array(abs(imgMeta3.zDif_r1sl_r2sr) > 15) &  np.array(abs(imgMeta3.zDif_r1sr_r2sl > 15)))]
outputs = [1]
# if height dif of > 15m between theoretical and real central point 
imgMeta3['topography_flag'] = np.select(conditions, outputs)
#%%
#drop unneeded columns
imgMeta3 = imgMeta3.drop([u'central_lat', u'central_lon', u'central_elev', u'r1sl_lat', u'r1sl_lon', u'r2sl_lat', u'r2sl_lon',
                       u'r1sr_lat', u'r1sr_lon', u'r2sr_lat', u'r2sr_lon', u'r1sl_elev',
                       u'r2sl_elev', u'r1sr_elev', u'r2sr_elev', u'zDif_r1sl_r2sr', u'zDif_r1sr_r2sl'], axis = 1)
# 
#%%
# write to a csv 
imgMeta3.to_csv('imageInterval/imageViewDomains.csv')
#%%
print('Process complete')
