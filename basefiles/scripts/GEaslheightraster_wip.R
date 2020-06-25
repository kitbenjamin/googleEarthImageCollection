library(yaml)
library(raster)
#get a rasterised dataset of google maps (GM heights)
#this currently works for the base files yaml config

#added comments for KB to finish starting: "KBtodo" (minor things)

#KBtodo: only test using coarse resolution (to save on api calls)

#KBtodo: make this a standalone script that runs after all images have been collected
#can still be sourced from within python

#KBtodo: put script etc in basefiles/scripts and source with relative path as per all other scripts
#not source basefiles as is seen here

setwd("C:/Users/micromet/Documents/GitHub/googleEarthImageCollection/")
params <- yaml::read_yaml("basefiles/metaData/imageCollectionConfig.yml")
source("basefiles/scripts/getAboveSeaLevelHeight.R")


#KBtodo: add the parameters to yaml
#what is the grid resolution of GM heights you want to obtain?
#heights are collectd at this resolution 
gridResolution_GM <- 50 #(m)
#extend the region by grid_extent_padding on each region side
grid_extent_padding <- 500 #(m)
#what is the final resolution of the raster you want. should be same order of magnitude as 
#gridResolution_GM (it can be higher res - it is interpolated)
rasterRes_final <- 25
#KBtodo: add the parameters to yaml /end


pointGrid_GE <- make_lat_lon_grid(latStart = params$regionArea$latStart, 
                                  lonStart = params$regionArea$lonStart, 
                                  grid_extent_padding = grid_extent_padding, 
                                  grid_resolution = gridResolution_GM)

pointGrid_sp <- SpatialPoints(pointGrid_GE[2:1], proj4string = CRS(params$projection))

pointGrid_sp_WGS84 <- spTransform(pointGrid_sp, CRS("+init=epsg:4326"))

#KBtodo make this a function GM_getAslRaster(x = "obj of class SpatialPoints")
pointGrid_df <- data.frame(pointGrid_sp_WGS84)
seq_ind <- seq(1, nrow(pointGrid_df), by = 250)
#preallocate
oMat <- matrix(nrow = nrow(pointGrid_df), ncol = 3)
for (i in 1:length(seq_ind)) {
  print(paste(i, "/", length(seq_ind)))
  from <- seq_ind[i]
  if (i == length(seq_ind)) {
    to <- nrow(pointGrid_df)
  } else {
    to <- seq_ind[i + 1]
  }
  ind <- from:to
  iter_vals <- GM_aslheight_api_call_chunk(data.frame(pointGrid_sp_WGS84)[ind,][2:1])
  tmp <- GM_format_api_result(iter_vals)
  oMat[ind, ] <- as.matrix(GM_format_api_result(iter_vals))
  Sys.sleep(1)
}

pointGrid_sp_WGS84_z <- SpatialPointsDataFrame(data.frame(oMat[,2:1]),
                                               data.frame("Z" = oMat[,3]), 
                                               proj4string = CRS("+init=epsg:4326"))

pointGrid_sp_UTM <- spTransform(pointGrid_sp_WGS84_z, CRS(params$projection))

raster_z <- raster()
extent(raster_z) <- extent(pointGrid_sp_UTM)
res(raster_z) <- rep(gridResolution_GM * 1.1, 2)
raster_z <- raster::rasterize(pointGrid_sp_UTM, raster_z, field = "Z")
raster_z_interp <- raster::disaggregate(raster_z, 
                                        fact = res(raster_z) / rasterRes_final, 
                                        method = 'bilinear')

if (any(is.na(raster_z[]))) stop("Missing GM heights: coarsen raster resolution [rasterRes_final]")

#KBtodo GM_getAslRaster()/end


#KBtodo change from plot to save raster as you see fit
plot(raster_z_interp, zlim = c(-10, 50))

