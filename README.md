# googleEarthImageCollection
Collect images from Google Earth that can be used to generate 3-D models.
---

## Requirements
#### Software:
     * Windows Powershell
     * Python 2.7
     * R 
     * Google Earth Pro
#### Packages:
     * Powershell: powershell-yaml
     * Python2.7: os, numpy, pandas, subprocess, shutil, re, pyyaml, pykml, lxml, pyproj
     * R: RCurl, RJSONIO
     
## Usage

1. To initiate a new collection region run the install.bat file. This will prompt you to name for your region. This will 
   then appear as a subdirectory in the *simulations* folder.
2. Configure your collection region and other parameters- such as the directories to Python, R and Google Earth in the 
   imageCollectionConfig.yml. This is in YAML format. To get the definitions of all parameters see wiki.
3. Run imageCollection.PS1 to collect all required Google Earth images. See wiki for more info on how to do this.

## Features
* 
