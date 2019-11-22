#%%
### load in modules ####
from pykml.factory import nsmap
from pykml.factory import KML_ElementMaker as KML
from pykml.factory import GX_ElementMaker as GX
from lxml import etree
import pandas as pd
import subprocess
import pyproj
import os
import numpy as np
import shutil
import re
import yaml
#%%
#set up directories
chunkfilepath = os.path.join('Chunks')
if os.path.exists(chunkfilepath) == True:
    shutil.rmtree(chunkfilepath)
    os.makedirs('Chunks')
else:
    os.makedirs('Chunks')

if os.path.exists('out') == False:
    os.makedirs('out')
    
if os.path.exists('googleEarthOut') == False:
    os.makedirs('googleEarthOut')
#%%
# gets camera metadata and writes to chunk csv
def create_chunklist(latPointsGrid, range0, altitudeMode, lookAtDuration):
    # get the camera positions required 
    chunklist=[]
    #create chunklist
    for i in xrange(0, len(latPointsGrid)):
        for v in xrange(0, len(latPointsGrid[i])):
            d = {}
            d['latitudeUTM'] = latPointsGrid[i][v]
            d['longitudeUTM'] = lonPointsGrid[i][v]
            d['range0'] = range0
            d['altitudeMode'] = altitudeMode
            d['lookAtDuration'] = lookAtDuration
            chunklist.append(d)
    return chunklist
#%%      
def create_chunck_csv(chunklist):    
    #create the original chunk csv
    #nThChunk - track the chunk number that we are on - need this to keep track of the camera ID numbers
    nThChunk = -1
    
    #create a master csv that has camera and image imrmation 
    for chunk in chunklist:
        nThChunk += 1
        chunk['longitude'], chunk['latitude'] = myProj(chunk['longitudeUTM'], chunk['latitudeUTM'], inverse = True)
        print(chunk)
        #run R script given the defined parameters for the current chunk - NEEDS UTM COORDINATES
        args = [str(chunk['longitudeUTM']), str(chunk['latitudeUTM']) , str(zenithAngles), str(pathLengths), 
                str(nSamplesAroundOrigin), str(chunk['latitude']), str(chunk['longitude']), str(nThChunk)]
        popenCmd = [RscriptLoc + str('Rscript.exe'), '--vanilla', '--no-save', 'scripts/rotateCameraAroundChunkOrigin.R']
        popenCmdwArgs = list(np.append(popenCmd, args))
        rotate = subprocess.Popen(popenCmdwArgs, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
        out, err = rotate.communicate()
        print(out)
        print(err)
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
def create_tour_doc(tour_doc, row, chunklist):
    camHeight  = row['Z']
    longitude, latitude = myProj(row['X'], row['Y'], inverse = True)
    azimuth = row['azimuth']
    zenith = row['zenith']
    
    chunkNo = row['ChunkNo']
    corrChunk = chunklist[int(chunkNo)]
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
    outFileName = 'out/' + str(KMLname + '.kml')
    outfile = open(outFileName, 'w')
    outfile.write(etree.tostring(tour_doc, pretty_print = True))
    outfile.close()

#%%
# moves all created images into their 'run' folders then move the chunck table also
def moveImagesToRun(n):
    imgsCreated = os.listdir('googleEarthOUT')
    if os.path.exists('googleEarthOUT/run'+str(n)+'') == False:
        os.mkdir('googleEarthOUT/run'+str(n)+'')
    for i in imgsCreated:
        if '.png' in i:
            shutil.move('googleEarthOUT/'+i+'', 'googleEarthOUT/run'+str(n)+'')
    
    chunkCSVs = os.listdir('Chunks')
    for i in chunkCSVs:
        sp = re.split("['_', '.']", i)
        if 'run' in sp[-2]:
            imgDir = 'googleEarthOUT/'+sp[-2]
            shutil.move('Chunks/'+i, imgDir)
#%% 
# runs google earth with a  kml file, based on what is to be completed
def get_GE_images(KMLname, toBeDone, n, is_rerun = False):
        if is_rerun == True:
            #find the number of images left to be created and their label
            nImgs = len(toBeDone)
            imgNs = np.arange(0,nImgs, 1)
            imgNames = ['movie-'+str(i).zfill(6)+'.png' for i in imgNs]
               
            #assign labels of what will be created 
            toBeDone.at[:,'Label'] = imgNames
        
        #Initiate new kml, starting from the right place
        KMLname = KMLname + '_' + str(n)
        tour_doc = init_kml(KMLname)
        
        # create the new tour doc
        toBeDoneGroup = toBeDone.groupby('ChunkNo')
        for name, group in toBeDoneGroup:
            for i, row in group.iterrows():
                create_tour_doc(tour_doc, row, chunklist)
        
        # create new kml
        write_kml(tour_doc, KMLname)
        
        #get the kml path
        wd = os.getcwd()
        kmlPath =  wd + '\\out\\'+KMLname+'.kml'
        
        #open google earth and check for google earth crash
        crashTest = subprocess.Popen([RscriptLoc + str('Rscript.exe'), '--vanilla', '--no-save', 'scripts/GEcrashTest.R', GEdir, kmlPath, str(GEtimeout)],
                                     stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
        
        out, err = crashTest.communicate()
        print(out)
        #print(err)
        endStatusSplit = list(out.split(" ")) 
        endStatus = endStatusSplit[-1].rstrip('\r|\n')
        #print(endStatus)
        
        #use end status to let user decide whether to re run
        if endStatus == '"aborted"':
            finish = input('Google Earth was aborted, was the movie maker finished? ["y"/"n"] ')
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
            print('Google Earth crashed, it shall now be reopened and movie maker can be re-run from the point of the crash')
            
        if endStatus == '"timedout"':
            finish = input('Google Earth timed out, was the movie maker finished? ["y"/"n"] ')
            if finish == 'y':
                rerun = False
                print('Google Earth will not be opened again')
            elif finish == 'n':
                rerun = True
                print('Google Earth will be reopened and movie maker can be re-run from the point of the timeout')
            else:
                print( 'unrecognised input, assuming movie maker unfinished. Google Earth will be reopened.')
                
        #check what has been created 
        imgsCreated = os.listdir('googleEarthOUT')
        chunkTab2 = toBeDone
        
        for i, row in chunkTab2.iterrows():
            if row['Label'] in imgsCreated:
                chunkTab2.at[i, 'Created'] = True
        
        #use created files to decide what is left to do
        chunkTabComplete = chunkTab2.loc[chunkTab2['Created'] == True]
        chunkTabComplete.to_csv('Chunks/chunk_table_run'+str(n)+'.csv', header = True, index = False)
                                
        toBeDoneNext = chunkTab2.loc[chunkTab2['Created'] == False]
        
        # move images 
        moveImagesToRun(n)
                            
        return rerun, toBeDoneNext 
#%%

####input parameters####
# load in configuration file
configPath = "metaData/imageCollectionConfig.yml"
with open(configPath) as file:
    meta = yaml.load(file, Loader=yaml.FullLoader)

##create a series of lat, lon values
#latitude sequence: this represents what would be a sequence of coordinates.
#Each coordinate represents the locaiton of an individual "chunk"
#of the surface processed by AgiSoft.


# define variables
collectionArea = meta['collectionArea']
#latitiudes
latstart = collectionArea['latStart']
latinterval = collectionArea['latInterval']
latend = latstart + latinterval
latstep = collectionArea['latStep']
latPoints = UTMseq(latstart, latend, latstep)

#longitudes
lonstart = collectionArea['lonStart']
loninterval = collectionArea['lonInterval']
lonend = lonstart + loninterval
lonstep = collectionArea['lonStep']
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
#%%
# test if there are multiple nSamples and zenith angles- if so manipulate them as required
if len(nSamplesAroundOrigin) > 1 and len(zenithAngles) > 1 and len(pathLengths) > 1:
    nSamplesAroundOrigin = ','.join([str(number) for number in nSamplesAroundOrigin]) 
    zenithAngles = ','.join([str(angle) for angle in zenithAngles]) 
    pathLengths = ','.join([str(length) for length in pathLengths]) 
elif len(nSamplesAroundOrigin) == 1 and len(zenithAngles) == 1 and len(pathLengths) == 1:
    nSamplesAroundOrigin = nSamplesAroundOrigin[0]
    zenithAngles = zenithAngles[0]
    pathLengths = pathLengths[0]
else:
    raise ValueError('zenithAngles, nSamplesAroundOrigin and pathLengths do not have same number of entries')
        
#%%   
#write the original chunk file with required camera metadata
chunklist = create_chunklist(latPointsGrid, range0, altitudeMode, lookAtDuration)
create_chunck_csv(chunklist)
#%%
# read in this file
chunkTab = pd.read_csv('Chunks/chunk_table_original.csv')
#n = 0 as is run zero
n = 0
# the first run
rerun, toBeDone = get_GE_images(KMLname, chunkTab, n, is_rerun = False)
#%%
#keep running until rerun = False
if len(toBeDone) > 0:
    n = 1
    while rerun == True:
        rerun, toBeDone = get_GE_images(KMLname, toBeDone, n, is_rerun = True)
        n += 1 #for naming new chunk table and kml
        if rerun != True:
            break
        # if been rerun multiple of 20 times ask if still want to continue
        if n % 20 == 0:
            finish = input('Google Earth has run ' +n+' times, would you like to continue the movie maker ["y"/"n"] ')
            if finish == 'y':
                rerun = True
            elif finish == 'n':
                rerun = False
            else:
                print('unrecognised input, will continue')
                rerun = True

#%%
print 'Images created. Image view domains will now be calculated...'
    