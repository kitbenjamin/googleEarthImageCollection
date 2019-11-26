# -*- coding: utf-8 -*-
"""
Created on Mon Nov 25 11:12:35 2019

@author: kitbe
"""
#%%
import os
import numpy as np
import pandas as pd
import re
import shutil
#%%
# execute the functions file
execfile('scripts/functions.py')
# get the input parameters
execfile('scripts/input_params.py')
#%%
# remove placeholder files 
directories = os.listdir(os.getcwd())
rmov = [os.remove(dire+'/placeholder.txt') for dire in directories if os.path.isdir(dire) and os.path.isfile(dire+'/placeholder.txt')]
# if can't find any alternative return stage 6 i.e no idea
stageCode = 6
crashPoint = 'Not sure whats going on'
#%% 
# read in data if exists- otherwise original table needs to be created
try:
    imgMeta = pd.read_csv('imageInterval/imageIntervalTable.csv')
except:
    stageCode = 0 
    crashpoint = 'Original image interval table not created'
#%%
#csv files in imageInterval directory
csvFiles = os.listdir('imageInterval')
# run folders/ images in googleEarthOut folder
geout = os.listdir('googleEarthOut')
# any imageIntervalTable_run files that haven't been moved into run folder
run_files = [fil for fil in csvFiles if 'run' in fil]
# any images that haven't been moved into run folder
unmovedimgs = [img for img in geout if '.png' in img]
runDirs = [dire for dire in geout if dire not in unmovedimgs]
#%%
# if everything is there- probs finished
if 'imageViewDomains.csv' in csvFiles and 'imageIntervalTable.csv' in csvFiles:
    stageCode = 5
    crashpoint = 'finished'
#%%
# if only view domains need to be finished
if 'imageIntervalTable.csv' in csvFiles and ('imageViewDomains.csv' in csvFiles) == False:
    stageCode = 4
    crashpoint = 'Everything created apart from view domains'
#%%
# in certain conditions program won't be at stage 4 or 5 
if stageCode == 4 or stageCode == 5:
    if len(run_files) > 0:
        # if there's a table run file but no images 
        if len(unmovedimgs) == 0:
            stageCode = 2
            crashpoint = 'csv has been created but images havent been created'
        # if run table and images need to be moved
        else:
            stageCode = 3
            crashpoint = 'images and run csv need to be moved'
    # if there should be images to create but there's no run file 
    elif len(run_files) == 0:
        nPhotos = np.sum([len(os.listdir('googleEarthOut'+'/'+i)) - 1 for i in runDirs])
        if len(imgMeta) > nPhotos:
            stageCode = 1
            crashpoint = 'csv for run hasnt been created'
            if len(unmovedimgs) > 0:
                stageCode = 1.5
                crashpoint = 'images have been created but csv needs to be written'
#%%
# find if a kml file has already been created so it can be deleted 
if len(run_files) > 0:
    runFile = run_files[0]
    latestRun = re.split("[ '_' | '.' ]", runFile)[1][3]

    kmlFiles = os.listdir('kmlFiles')    
    runKML = [i for i in kmlFiles if latestRun in i]
#%%
# find what needs to be done as well as finding the runNo
# n is zero unless there have already been runs
n = 0
if len(runDirs) > 0:
    runNo = []
    runDirs = [i for i in geout if os.path.isdir('googleEarthOut/'+i)]
    firstRun = runDirs[0]
    if stageCode != 0:
        runCsvData = pd.read_csv('googleEarthOut/'+firstRun+'/imageIntervalTable_'+firstRun+'.csv')
        runNo.append(0)
        runCsvData['run'] = firstRun
        for i in runDirs[1:]:
            runDF = pd.read_csv('googleEarthOut/'+i+'/imageIntervalTable_'+i+'.csv')
            runDF['run'] = i
            runNo.append(int(i[3]))
            runCsvData = pd.concat([runCsvData, runDF], axis = 0, ignore_index=True)
        toBeDone = imgMeta.iloc[len(runCsvData):]
        n = max(runNo) + 1
#%%
#fixing 
if stageCode == 0:
    execfile('scripts/kmlCreator.py')
    execfile('scripts/calcViewDomain.py')
else:
    # give user option to continue-> is not delete and start again
    cont = input('Existing simulation components have been detected. Do you want to continue this simulation ["y"/"n"] ')
    if cont == 'y':
        print('Will attempt to continue')
        print('Stage prior to crash: ' + crashpoint)
        attempt_continue(stageCode, toBeDone, n)
        if stageCode < 5: #stage 5 is all complete so don't bother calculating view domains again
            execfile('scripts/calcViewDomain.py')
    elif cont == 'n':
        print('Deleting existing components')
        dirs = ['googleEarthOut', 'imageInterval', 'kmlFiles']
        [shutil.rmtree(dire) for dire in dirs if os.path.exists(dire)]
        [os.mkdir(dire) for dire in dirs]