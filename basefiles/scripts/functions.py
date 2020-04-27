# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 11:21:16 2019

@author: kitbe
"""
#%%
### load in modules ####
from pykml.factory import nsmap
from pykml.factory import KML_ElementMaker as KML
from pykml.factory import GX_ElementMaker as GX
from lxml import etree
import subprocess
import os
import numpy as np
import shutil
import re
#%%
#=== kml creator functions === 
#%%
# gets camera metadata and writes to chunk csv
def create_imageInterval(latPointsGrid, lonPointsGrid, range0, altitudeMode, lookAtDuration):
    # get the camera positions required 
    imageInterval=[]
    #import pdb; pdb.set_trace()
    #create chunklist
    for i in xrange(0, len(latPointsGrid)):
	    #make "lawnmower" pattern back and forth along lat
        if i % 2 == 0:
            latRange = xrange(0, len(latPointsGrid[i]))
        else:
            latRange = reversed(xrange(0, len(latPointsGrid[i])))
        for v in latRange:
            d = {}
            d['latitudeUTM'] = latPointsGrid[i][v]
            d['longitudeUTM'] = lonPointsGrid[i][v]
            d['range0'] = range0
            d['altitudeMode'] = altitudeMode
            d['lookAtDuration'] = lookAtDuration
            imageInterval.append(d)
    return imageInterval
#%%      
def create_imageInterval_csv(imageInterval, zenithAngles, pathLengths, nSamplesAroundOrigin):    
    #create the original chunk csv
    #nThChunk - track the chunk number that we are on - need this to keep track of the camera ID numbers
    nThChunk = -1
    #create a master csv that has camera and image imrmation 
    for chunk in imageInterval:
        nThChunk += 1
        chunk['longitude'], chunk['latitude'] = myProj(chunk['longitudeUTM'], chunk['latitudeUTM'], inverse = True)
        print('Interval number: ' + str(nThChunk) +'/'+str(len(imageInterval) - 1))
        print(chunk)
        #run R script given the defined parameters for the current chunk - NEEDS UTM COORDINATES
        args = [str(chunk['longitudeUTM']), str(chunk['latitudeUTM']) , str(zenithAngles), str(pathLengths), 
                str(nSamplesAroundOrigin), str(chunk['latitude']), str(chunk['longitude']), str(nThChunk)]
        popenCmd = [RscriptLoc + str('Rscript.exe'), '--vanilla', '--no-environ', '--no-init-file', 'scripts/rotateCameraAroundChunkOrigin.R']
        popenCmdwArgs = list(np.append(popenCmd, args))
        rotate = subprocess.Popen(popenCmdwArgs, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
        out, err = rotate.communicate()
        #print(out)
        #print(err)
#%%
# function to create sequence of lats/lons
def UTMseq(start, end, step):
        start = start * 100
        end = end * 100
        step = step * 100
        OUT=xrange(start, end, step)
        OUTm = np.array(OUT)/100
        return OUTm
#%%
# kml functions
def init_kml(KMLname):
    # start with a base KML tour and playlist
    tour_doc = KML.kml(
        KML.Document(
          GX.Tour(
            KML.name(KMLname),
            GX.Playlist(),
    		),
        )
    )
    return tour_doc
#%%
def create_tour_doc(tour_doc, row, imageInterval):
    camHeight  = row['Z']
    longitude, latitude = myProj(row['X'], row['Y'], inverse = True)
    azimuth = row['azimuth']
    zenith = row['zenith']
    
    intervalNo = row['intervalNo']
    corrChunk = imageInterval[int(intervalNo)]
    # define a variable for the Google Extensions namespace URL string
    gxns = '{' + nsmap['gx'] + '}'
    #fly to the subChunk with the given subChunk parameters
    tour_doc.Document[gxns+"Tour"].Playlist.append(
        GX.FlyTo(
            GX.flyToMode("bounce"),
            KML.LookAt(
                KML.longitude(longitude),#change  chunk[] to subChunk from csv
                KML.latitude(latitude),#change  chunk[] to subChunk from csv
                KML.altitude(camHeight),#change  chunk[] to subChunk from csv
                KML.heading(azimuth),#change chunk[] to subChunk from csv
                KML.tilt(zenith),#change  chunk[] to subChunk from csv
                KML.range(corrChunk['range0']),#change all chunk[] to subChunk from csv
                KML.altitudeMode(corrChunk['altitudeMode']),
    						GX.horizFov(horizFov)
            )
        )
    )
    tour_doc.Document[gxns+"Tour"].Playlist.append(GX.Wait(GX.duration(corrChunk['lookAtDuration'])))
#%%
def write_kml(tour_doc, KMLname):
    #output a KML file (named based on the Python script)
    outFileName = 'kmlFiles/' + str(KMLname + '.kml')
    outfile = open(outFileName, 'w')
    outfile.write(etree.tostring(tour_doc, pretty_print = True))
    outfile.close()

#%%
# moves all created images into their 'run' folders then move the chunck table also
def moveImagesToRun(n):
    imgsCreated = os.listdir('googleEarthOut')
    if os.path.exists('googleEarthOut/run'+str(n)+'') == False:
        os.mkdir('googleEarthOut/run'+str(n)+'')
    else:
        runFiles = os.listdir('googleEarthOut/run'+str(n)+'')
        if len(runFiles) > 0:
            [os.unlink('googleEarthOut/run'+str(n)+'/'+fil) for fil in runFiles]
    for i in imgsCreated:
        if '.png' in i:
            shutil.move('googleEarthOut/'+i+'', 'googleEarthOut/run'+str(n)+'')
    
    imgCSVs = os.listdir('imageInterval')
    for i in imgCSVs:
        sp = re.split("['_', '.']", i)
        if 'run' in sp[-2]:
            imgDir = 'googleEarthOut/'+sp[-2]
            shutil.move('imageInterval/'+i, imgDir)
#%%
def assign_labels(toBeDone1):
    nImgs = len(toBeDone1)
    imgNs = np.arange(0,nImgs, 1)
    imgNames = ['movie-'+str(i).zfill(6)+'.png' for i in imgNs]
    toBeDone = toBeDone1.copy()
    #assign labels of what will be created 
    toBeDone.at[:,'Label'] = imgNames
    return toBeDone
#%%
def gen_kml(KMLname, toBeDone, n, imageInterval):
    #Initiate new kml, starting from the right place
    KMLname = KMLname + '_' + str(n)
    tour_doc = init_kml(KMLname)
    
    # create the new tour doc
    toBeDoneGroup = toBeDone.groupby('intervalNo')
    for name, group in toBeDoneGroup:
        for i, row in group.iterrows():
            create_tour_doc(tour_doc, row, imageInterval)
    
    # create new kml
    write_kml(tour_doc, KMLname)
    
    #get the kml path
    wd = os.getcwd()
    kmlPath =  wd + '\\kmlFiles\\'+KMLname+'.kml'
    return kmlPath
#%%
def run_google_earth(kmlPath):
     #open google earth and check for google earth crash
    crashTest = subprocess.Popen([RscriptLoc + str('Rscript.exe'), '--vanilla', '--no-save', 'scripts/GEcrashTest.R', GEdir, kmlPath, str(GEtimeout)],
                                 stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
    
    out, err = crashTest.communicate()
    print(out)
    #print(err)
    endStatusSplit = list(out.split(" ")) 
    endStatus = endStatusSplit[-1].rstrip('\r|\n')
    return endStatus
#%%
def user_rerun_decide(endStatus):
            #use end status to let user decide whether to re run
    if endStatus == '"aborted"':
        finish = raw_input('Google Earth was aborted, was the movie maker finished? [y/n] ')
        if finish == 'y':
            rerun = False
            print('Google Earth will not be opened again')
        elif finish == 'n':
            rerun = True
            print('Google Earth will be reopened and movie maker can be re-run from the point of the abort')
        else:
            print( 'unrecognised input, assuming movie maker unfinished. Google Earth will be reopened.')
    
    if endStatus == '"crashed"':
        rerun = True
        remove_last_image()
        print('Google Earth crashed, it shall now be reopened and movie maker can be re-run from the point of the crash')
        
    if endStatus == '"timedout"':
        finish = raw_input('Google Earth timed out, was the movie maker finished? [y/n] ')
        if finish == 'y':
            rerun = False
            print('Google Earth will not be opened again')
        elif finish == 'n':
            rerun = True
            remove_last_image()
            print('Google Earth will be reopened and movie maker can be re-run from the point of the timeout')
        else:
            print( 'unrecognised input, assuming movie maker unfinished. Google Earth will be reopened.')
    return rerun
#%%
def get_toBeDoneNext(toBeDone, n):
    #check what has been created 
    imgsCreated = os.listdir('googleEarthOut')
    imgTab2 = toBeDone.copy()
    
    for i, row in imgTab2.iterrows():
        if row['Label'] in imgsCreated:
            imgTab2.at[i, 'Created'] = True
    
    #use created files to decide what is left to do
    imgTabComplete = imgTab2.loc[imgTab2['Created'] == True]
    imgTabComplete.to_csv('imageInterval/imageIntervalTable_run'+str(n)+'.csv', header = True, index = False)
                            
    toBeDoneNext = imgTab2.loc[imgTab2['Created'] == False]
    return toBeDoneNext
#%% 
# runs google earth with a  kml file, based on what is to be completed
def get_GE_images(KMLname, toBeDone, n, imageInterval, is_rerun = False):
    if is_rerun == True:
        #find the number of images left to be created and their label
        toBeDone = assign_labels(toBeDone)
    
    kmlPath = gen_kml(KMLname,toBeDone, n, imageInterval)
    
    endStatus = run_google_earth(kmlPath)
    
    rerun = user_rerun_decide(endStatus)
    
    toBeDoneNext = get_toBeDoneNext(toBeDone, n)
    
    # move images 
    moveImagesToRun(n)
                        
    return rerun, toBeDoneNext 
#%%
def rerun_get_GE_images(KMLname, imgTab, n, imageInterval, ps_crash = False):
    # the first run
    if ps_crash == False:
        rerun, toBeDone = get_GE_images(KMLname, imgTab, n, imageInterval, is_rerun = False)
    elif ps_crash == True:
        rerun, toBeDone = get_GE_images(KMLname, imgTab, n, imageInterval, is_rerun = True)
    #keep running until rerun = False
    if len(toBeDone) > 0:
        n += 1
        while rerun == True:
            rerun, toBeDone = get_GE_images(KMLname, toBeDone, n, imageInterval, is_rerun = True)
            n += 1 #for naming new chunk table and kml
            if rerun != True:
                break
            # if been rerun multiple of 20 times ask if still want to continue
            if n % 20 == 0:
                finish = raw_input('Google Earth has run ' +n+' times, would you like to continue the movie maker [y/n] ')
                if finish == 'y':
                    rerun = True
                elif finish == 'n':
                    rerun = False
                else:
                    print('unrecognised input, will continue')
                    rerun = True
        # only remove the last image if the process was completed
        else:
           if len(toBeDone) == 0:
               remove_repeated_image()
    else:
        remove_repeated_image()
#%%
def remove_repeated_image():
    runDirs = os.listdir('googleEarthOut')
    runn = [int(i[3]) for i in runDirs if 'run' in i and len(i) == 4]
    lastRun = 'run'+str(max(runn))
    lastRunImgs = [i for i in os.listdir('googleEarthOut/'+lastRun) if '.png' in i]
    imgNumbs = [int(re.split("[.,-]", i)[1]) for i in lastRunImgs]
    repeatedImg = 'movie-'+str(max(imgNumbs)).zfill(6)+'.png'
    os.remove('googleEarthOut/'+lastRun+'/'+repeatedImg)
#%%
#=== calculate view domain functions ===
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
            outfile = open('kmlFiles/viewDomains/'+str(run)+'/'+str(row['Label'])+'_adj.kml', 'w')
        else: 
            outfile = open('kmlFiles/viewDomains/'+str(run)+'/'+str(row['Label'])+'.kml', 'w')
        outfile.write(etree.tostring(polygon_kml, pretty_print = True)) 
        outfile.close()
#%%
def assertSameCoords(dataframe, elevations, index, noDP):
    assert abs(float(elevations[index][0]) - round(dataframe.loc[index, 'central_lat'], noDP[0])) < 10**noDP[0] and abs(float(elevations[index][1]) - round(dataframe.loc[index, 'central_lon'], noDP[1])) < 10**noDP[1]
    assert abs(float(elevations[index][3]) - round(dataframe.loc[index, 'r1sl_lat'], noDP[2])) < 10**noDP[2] and abs(float(elevations[index][4]) - round(dataframe.loc[index, 'r1sl_lon'], noDP[3])) < 10**noDP[3]
    assert abs(float(elevations[index][6]) - round(dataframe.loc[index, 'r2sl_lat'], noDP[4])) < 10**noDP[4] and abs(float(elevations[index][7]) - round(dataframe.loc[index, 'r2sl_lon'], noDP[5])) < 10**noDP[5]
    assert abs(float(elevations[index][9]) - round(dataframe.loc[index, 'r1sr_lat'], noDP[6])) < 10**noDP[6] and abs(float(elevations[index][10]) - round(dataframe.loc[index, 'r1sr_lon'], noDP[7])) < 10**noDP[7]
    assert abs(float(elevations[index][12]) - round(dataframe.loc[index, 'r2sr_lat'], noDP[8])) < 10**noDP[8] and abs(float(elevations[index][13]) - round(dataframe.loc[index, 'r2sr_lon'], noDP[9])) < 10**noDP[9]
#=== imp kml create ===
#%%
def attempt_continue(stageCode, toBeDone, n):
    # if the run csv hasn't been created then create and run
    if stageCode == 1: 
        imageInterval = create_imageInterval(latPointsGrid, lonPointsGrid, range0, altitudeMode, lookAtDuration)
        if n == 0: 
            rerun_get_GE_images(KMLname, imgMeta, n, imageInterval, ps_crash = True)
        else:
            rerun_get_GE_images(KMLname, toBeDone, n, imageInterval, ps_crash = True)
    
    # if images created but run csv not (most likely) create csv and carry on 
    if stageCode == 1.5:
        if n == 0:
            toBeDone = imgMeta
        else: 
            toBeDone = imgMeta.iloc[int(nPhotos):]
            toBeDone = assign_labels(toBeDone)
        endStatus = '"aborted"'
        user_rerun_decide(endStatus)
        toBeDoneNext = get_toBeDoneNext(toBeDone, n)
        moveImagesToRun(n)
        n += 1
        imageInterval = create_imageInterval(latPointsGrid, lonPointsGrid, range0, altitudeMode, lookAtDuration)
        rerun_get_GE_images(KMLname, toBeDoneNext, n, imageInterval, ps_crash = True)
    
    # if run csv created but images not (been silly and now don't think this is possible)
    if stageCode == 2:
        imageInterval = create_imageInterval(latPointsGrid, lonPointsGrid, range0, altitudeMode, lookAtDuration)
        if len(runKML) > 0:
            os.remove('KMLfiles/'+runKML[0])
        kmlPath = gen_kml(KMLname,toBeDone, n)
        endStatus = run_google_earth(kmlPath)
        rerun = user_rerun_decide(endStatus)
        toBeDoneNext = get_toBeDoneNext(toBeDone, n)
        # move images 
        moveImagesToRun(n)
        if rerun == True:
            n+=1
            rerun_get_GE_images(KMLname, toBeDoneNext, n, imageInterval, ps_crash = True)
    
    # if images and run csv haven't been moved then move them and carry on
    if stageCode == 3:
        images_to_move = [i for i in geout if i not in runDirs]
        moveImagesToRun(n)
        toBeDoneNext = toBeDone.iloc[len(images_to_move):]
        if len(toBeDoneNext) > 0:
            n+=1
            imageInterval = create_imageInterval(latPointsGrid, lonPointsGrid, range0, altitudeMode, lookAtDuration)
            rerun_get_GE_images(KMLname, toBeDoneNext, n, imageInterval, ps_crash = True)
    
    # if view domains hasn't been created
    if stageCode == 4:
        print('View domains will be calculated')
    # if everything looks like it's created do nothing
    if stageCode == 5:
        print('All appears to be created, please review files in simulation directory and delete any unneeded files.')
    # if soethings gone really wrong
    if stageCode == 6:
        print('please review files in simulation directory and delete any unneeded files.')

def remove_last_image():
    #remove last image taken by GE. should be done when GE crashes.
    files = [f for f in os.listdir('googleEarthOut') if re.match(r'movie*', f)]
    if len(files) > 0:
        os.remove(os.path.join('googleEarthOut', files[-1:][0]))

