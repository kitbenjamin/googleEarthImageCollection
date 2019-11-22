#require RCurl
#require RJSONIO
require(stringr)
require(data.table)

source(file.path("scripts", "getAboveSeaLevelHeight.R"))
args <- commandArgs(trailingOnly = TRUE)
#args are: [cx, cy, zenithAngles, pathLength, nSamplesRoundOrigin] in the following format:
cx <- as.numeric(args[1]) #chunk x origin
cy <- as.numeric(args[2]) #chunk y origin
zenithAngles <- as.numeric(strsplit(args[3], ",")[[1]])
pathLengths <- as.numeric(strsplit(args[4], ",")[[1]]) #what is the camera - origin path length that you want?
nSamplesAroundOrigin <- as.numeric(strsplit(args[5], ",")[[1]]) 

#what angular resolution n do you want around the point i.e. n = 360/nSamplesAroundOrigin
WGS84lat <- as.numeric(args[6]) #wgs lat - for height calc
WGS84lon <- as.numeric(args[7]) #wgs lon - for height calc
nThChunk <- as.numeric(args[8]) #what chunk is this within the main routine?


#define the camera height for each azimuth angle- assuming a flat surface within the chunk
#the predefined camera azimuth angle is then given, along with the predefined path length
#which is the distance between point [cx,cy] and the camera. 
#then use trig to find the height of the camera above ground (cameraHeight)
#and distance of the camera from [cx,cy] [cameraRadius) for the given azimuth angle
#do some trig for camera height and camera distance from central point
azimuthDiff <- 180 - 90 - zenithAngles
sinAzimuthDiff <- sin(azimuthDiff * (pi/180)) 
cosAzimuthDiff <- cos(azimuthDiff * (pi/180)) 
cameraHeightAGL <- sinAzimuthDiff * pathLengths
heightMETA <- getHeightAboveSeaLevelFromGoogleAPI(WGS84lat, WGS84lon)
ASLheight <- round(heightMETA["elevation"], 2)

cameraHeightASL <- cameraHeightAGL + ASLheight
cameraRadius <- cosAzimuthDiff * pathLengths

DAT <- list()
DATind <- 0
for(i in 1:length(cameraHeightASL)){
  for(a in seq(0, 350, 360 / nSamplesAroundOrigin[i])){
    DATind <- DATind + 1
    #turn the angle from center point 180 degrees, so looking at center point
    #also shift 90 degrees to get to Grid North as this is currently trig "north"
    azimuth <-  270 - a 
    if(azimuth < 0){
      azimuth <- azimuth + 360
    }
    DAT[[DATind]] <- data.frame("Z" = cameraHeightASL[i], 
                                "X" = cx + (cameraRadius[i] * cos(a * (pi / 180))), 
                                "Y" = cy + (cameraRadius[i] * sin(a * (pi / 180))),
                                "zenith" = round(zenithAngles[i], 2),
                                "azimuth" = round(azimuth, 2),
                                "roll" = 0,
                                "Z_ground" = ASLheight,
                                "chunkCentre" = paste0('[', cx, ', ', cy, ', ', ASLheight, ']'))
  }
}

DATOUT <- do.call(rbind, DAT)
DATOUT['Created'] <- FALSE
DATOUT['ChunkNo'] <- nThChunk

firstImageID <- ((nThChunk) * nrow(DATOUT)) 
imageIDs <- seq(firstImageID, length.out = nrow(DATOUT), by = 1)
imageIDs <- stringr::str_pad(imageIDs, 6, pad = '0')
DATOUT["Label"] <- paste("movie-", imageIDs, ".png", sep = "")

DATOUT <- setDT(DATOUT)

OUTFILE <- 'chunk_table_original.csv'
OUTPATH <- 'Chunks'
if(!dir.exists(OUTPATH)) dir.create(OUTPATH, recursive = TRUE)
write.table(x = DATOUT, file = file.path(OUTPATH, OUTFILE), sep = ",", col.names = !file.exists(file.path(OUTPATH, OUTFILE)), 
            append = T, row.names = FALSE)
