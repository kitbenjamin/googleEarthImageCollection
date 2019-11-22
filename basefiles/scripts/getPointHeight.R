# input as many (lat, lon)'s as possible and return height from google maps api
source(file.path("scripts", "getAboveSeaLevelHeight.R"))
args <- commandArgs(trailingOnly = TRUE)

# final number is the number of times python has called this script (only ~400 args allowed for some reason)
runNumber <- as.numeric(args[length(args)])
#remaining args
args = args[1:length(args) -1]
#turn to array with 2 cols
dim(args) <- c(2, length(args)/2)
args <- t(args)
# find the elevation of each point
elevs = getMultipleHeightAboveSeaLevelFromGoogleAPI(args)
print(elevs)


