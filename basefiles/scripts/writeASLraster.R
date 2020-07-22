library(yaml)
library(raster)
#get a rasterised dataset of google maps (GM) heights

params <- yaml::read_yaml("metaData/imageCollectionConfig.yml")
if (is.null(params$googleEarthOptions)) stop("Outdated meta data file.")

source("scripts/getAboveSeaLevelHeight.R")

gridResolution_GM <- params$googleMapsOptions$gridResolution
grid_extent_padding <- params$googleMapsOptions$gridExtentPadding
rasterRes_final <- params$googleMapsOptions$rasterResFinal

raster_z_interp <- getASLraster(latStart = params$regionArea$latStart, 
             lonStart = params$regionArea$lonStart, 
             grid_extent_padding = grid_extent_padding, 
             grid_resolution = gridResolution_GM, 
             CRSstring = params$projection)

writeRaster(x = raster_z_interp, 
            filename = "metaData/GM_heights.tiff",
            compression = "lzw", overwrite = TRUE)
