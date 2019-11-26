#%%
### load in modules ####
import pandas as pd
import os
import shutil
#%%
# get all the required functions
execfile('scripts/functions.py')
# get the input parameters
execfile('scripts/input_params.py')
#%%
#set up directories
imgintfilepath = os.path.join('imageInterval')
if os.path.exists(imgintfilepath) == True:
    shutil.rmtree(imgintfilepath)
    os.makedirs('imageInterval')
else:
    os.makedirs('imageInterval')

if os.path.exists('kmlFiles') == False:
    os.makedirs('kmlFiles')
    
if os.path.exists('googleEarthOut') == False:
    os.makedirs('googleEarthOut')
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
imageInterval = create_imageInterval(latPointsGrid, lonPointsGrid, range0, altitudeMode, lookAtDuration)
create_imageInterval_csv(imageInterval, zenithAngles, pathLengths, nSamplesAroundOrigin)  
#%%
# read in this file
imgTab = pd.read_csv('imageInterval/imageIntervalTable.csv')
#%%
#n = 0 as is run zero
n = 0
#get the google earth images
rerun_get_GE_images(KMLname, imgTab, n, imageInterval = imageInterval)
#%%
print 'Images created. Image view domains will now be calculated...'
    