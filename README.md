# googleEarthImageCollection
Collect images from Google Earth that can be used to generate 3-D models.
---

## Dependencies
### Software:
     * Windows Powershell
     * Python 2.7
     * R 
     * Google Earth Pro
### Packages:
     * Powershell: powershell-yaml
     * Python2.7: numpy, pandas, pyyaml, pykml, lxml, pyproj
     * R: RCurl, RJSONIO
     
## Install python packages
Install pip with e.g.:
```
C:/Python27/python.exe get-pip.py
```
with get-pip.py found in this repository.

Make sure you have PROJ, get it via osgeo: http://download.osgeo.org/osgeo4w/osgeo4w-setup-x86_64.exe
Then install packages:

```
C:/Python27/Scripts/pip.exe install numpy pandas pyyaml pykml lxml pyproj
 ```
 
## Install R packages
Open R and type:
```
install.packages(c("RCurl", "RJSONIO"))
```
   
## Usage
1. To initiate a new collection region run the install.bat file. This will prompt you to name for your region. This will 
   then appear as a subdirectory in the *simulations* folder.
2. Configure your collection region and other parameters- such as the directories to Python, R and Google Earth in the 
   imageCollectionConfig.yml. This is in YAML format. To get the definitions of all parameters see below.
3. Run imageCollection.PS1 to collect all required Google Earth images and calculate their view domains. See wiki for more info on how to do this.

## Features
* Collect images from Google Earth for a specified area.
* If Google Earth crashes, Google Earth will restart from the point of the crash.
* Viewing domain, or source area, of each image is calculated. This is adjusted for height. The height adjustment is least effective in non-uniform terrain so a flag is given is this is detected. Users should consider a higher density of images for these areas. This can later be used to help create high quality models of a selected area, using these collected images.  
* If process breaks, e.g. powershell crashes, the program will try and detect at which stage it broke restart from there.

## Instructions
### A. image collection
- The meta data, such as the collection area, for the Google Earth image collection is defined in the imageCollectionConfig.yml file within the 'metaData' directory.   
- After configuring the image collection, imageCollection.PS1 is run. Firstly, this will create the imageIntervalTable.csv file within the 'imageInterval' directory. This file contains information on the camera position of all images that will be created, given the meta data provided.
- A KML file is also generated that is automatically loaded into Google Earth. Using this KML, a sequence of images of the specified area can be created. To do this refer to the wiki. Images must be saved in the 'googleEarthOut' dierectory.
- When google earth is quit, crashes or timesout, the user is asked whether the image collection had finished. At this point the user must answer 'y' or 'n' acordingly. If yes then google earth of re-opened with a new KML loaded, picking up where the previous left off. This will keep happening until all images are created or the user specifies 'n'.
- If powershell is quit or fails during the image collection then imageCollection.PS1 will try an identify where to restart the program and ask the user whether to restart here. 
- Images are stored in the 'googleEarthOut' directory and then in a sub-directory created depending on which time google earth was run (i.e. run0 is the first time google earth was opened, run1 the second ect). Also within the sub-directory is the imageIntervalTable_runN.csv file which corresponds each image to a camera position.

### B. getting the view domain of each image 
- The next step is to calculate an idealised view domain. This is the area that would be covered by the image if the camera was looking at a perfectly flat area at sea level. This is calculated using trigonometry. Central is the point the camera is focussed on. The other points that encapsule the view domain are r1sl, r1sr, r2sr, r2sl. To understand what these mean consider r to be in the direction away from the camera (1 being closer than 2) and s to be the direction perpendicular to the camera (r and l being right and left respectively). See figures below for visual representations of this.  
![alt text](images/viewDomCalc1.png)
![alt text](images/viewDomCalc2.png)

- As these points are based on an idealised situation they are generally not accurate in the real world. Therefore, a height correction must be made. This is done using the following steps:
  1. Get the height of each point from the google maps api 
  2. For each point, create a 2D plane that intersects the point and the two points adjacent to it (e.g. for r1sl the plane will be calculated using the coordinates of r1sl, r1sr and r2sl).
  3. then, the point of intersection between this plane and the line from the camera to the point gives a height adjusted point (rNsD_adjusted).
- **This height correction is not accurate in complex terrain.** This is the reason a 'topography flag' is given in these situations. This is derived by finding the height difference between height of the central point given by the google maps API and the theoretical height derived by calculating the height the central point would have if it was on each of the planes. If the difference is greater than 15m for all planes the land surface is considered non-planar enough such that the adjusted view domain calculation will be significantly affected. in this situation the user is reccomended to take more images of the area.
- All this imformation can be found in viewDomains.csv in the 'imageInterval' directory. 

## Configuration parameters
All of these are parameters that define the area that is collected and how the images will appear.

| Parameter | Description | Units |
| --------- | ----------- | ----- |
| projection | The coordinate system that you are using to define your collection area. This should be in the form of a proj4 string, such as the default projection in imageCollectionConfig.yml | NA |
|  Latstart/Lonstart | The UTM lat/lon coordinate for the bottom left corner of the full domain. Might be useful to use https://epsg.io/map [or similar] to get an idea of the UTM coordinates needed. | m |
|  latinterval/loninterval |  The size of the domain in lat/lon axis | m |
|  latstep/lonstep | The resolution of each interval in lon/lat axis. The distance is measured from the XY center of each interval. If the step is not divisble by the interval [latinterval/loninterval], the number of steps will be rounded up. | m |
| horizFov |  Horizontal field of view of google earth tour camera. | degrees | 
| range0 | Unsure of function- keep to zero [default] | No idea |
| altitudeMode | How the height of the camera is determined i.e. for absolute the camera height is measured from a height of zero as opposed to ground level | NA |
| lookAtDuration |  How long does the google earth tour camera look at a given location? Default is 1 second. Only play with this if there are issues with google earth. Other elements of the program routine will need to be edited if this parameter is changed. E.g. if changing to 1s then you will need to run the google earth "movie" at 1 fps rather that 10 fps for 0.1s . | seconds |
| zenithAngles | Zenith angles of the camera. Takes multiple inputs. Use in conjunction with multiple 'nSamplesAroundOrigin' and 'pathLengths' | degrees | 
| nSamplesAroundOrigin | number of images to be taken around each zenithAngle. Use in conjunction with multiple 'zenithAngles' and 'pathLengths'| NA |
| pathLengths | The path length between the camera and the center of the chunk. The center of the chunk is adjusted to be above sea level. Use in conjunction with 'zenithAngles' and 'nSamplesAroundOrigin' | m |

#### Using multiple zenith angles, path lengths and samples around origin
The parameters 'zenithAngles', 'nSamplesAroundOrigin' and 'pathLengths' **must all have the same number of inputs**. Multiple inputs are given to a parameter like so: 
```
cameraOptions:
   zenithAngles:
   - 0
   - 45
 ```
 If you wanted to tke images at zenith angles 0 and 45. Correspondingly, nSamplesAroundOrigin and pathLengths must also have 2 arguments in this scenario. For example if you had zenithAngles $\vec{(0, 45)}$, as above,  nSamplesAroundOrigin \vec{-1, -10} and pathLengths \vec{(-360, -260)} you would have one image at 0 degrees from 360 metres and 10 at 45 degrees from 260 metres. 
