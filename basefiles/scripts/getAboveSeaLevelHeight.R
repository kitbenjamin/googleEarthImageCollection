rawHeightAboveSeaLevelHeightFromGoogleAPI <- function(WGS84lat, WGS84lon, return.call = "json", 
                                                      apiKey = "AIzaSyDiklf_BgSg67hfNzrJXEWeNcgrOXQzRGY",
                                                      verbose = FALSE){
  suppressWarnings(suppressMessages(require(RCurl)))
  suppressWarnings(suppressMessages(require(RJSONIO)))
  #get *single* height above sea level [has capability of multiple returns but CBA]
  root <- "https://maps.googleapis.com/maps/api/elevation/"
  address <- paste(root, return.call, "?locations=", WGS84lat, ",",WGS84lon, "&key=",apiKey, sep = "")
  if (verbose) print(address)
  doc <- getURL(address)
  x <- fromJSON(doc,simplify = FALSE)
  if (x$status != "OK") stop("apiKey error")
  return(x)
}

formatHeightAboveSeaLevelHeightFromGoogleAPI <- function(heightJSON){
  #return *single* height above sea level [has capability of multiple returns but CBA]
  
  return(c("lat" = heightJSON[[1]][[1]]$location$lat, "lon" = heightJSON[[1]][[1]]$location$lng, "elevation" = heightJSON[[1]][[1]]$elevation))
}


getHeightAboveSeaLevelFromGoogleAPI <- function(WGS84lat, WGS84lon, return.call = "json", 
                                                apiKey = "AIzaSyDiklf_BgSg67hfNzrJXEWeNcgrOXQzRGY",
                                                verbose = FALSE){
  
  heightJSON <- rawHeightAboveSeaLevelHeightFromGoogleAPI(WGS84lat, WGS84lon)
  return(formatHeightAboveSeaLevelHeightFromGoogleAPI(heightJSON))
}


GM_aslheight_api_call_chunk <- function(twoDlatlons, return.call = "json", 
                                        apiKey = "AIzaSyDiklf_BgSg67hfNzrJXEWeNcgrOXQzRGY",
                                        verbose = FALSE, latlonDigits = 7){
  
  suppressWarnings(suppressMessages(require(RCurl)))
  suppressWarnings(suppressMessages(require(RJSONIO)))
  twoDlatlons_digits <- apply(twoDlatlons, 2, function(x) format(x, digits = latlonDigits, scientific = FALSE))
  pasted <- apply(twoDlatlons_digits, 1, function(x){paste0(x[1], ',', x[2])})
  toSubmit <- gsub(" ", "", paste0(pasted, collapse = '|'))
  #get *single* height above sea level [has capability of multiple returns but CBA]
  root <- "https://maps.googleapis.com/maps/api/elevation/"
  address <- paste(root, return.call, "?locations=", toSubmit, "&key=", apiKey, sep = "")
  if (verbose) print(address)
  doc <- getURL(address)
  x <- fromJSON(doc, simplify = FALSE)
  if (x$status != "OK") stop("apiKey error")
  return(x)
}

GM_format_api_result <- function(GM_call_result) {
  
  lat_lon <-  do.call(rbind, lapply(GM_call_result$results, function(x) t(x$location)))
  Z <-  sapply(GM_call_result$results, function(x) x$elevation)
  return(data.frame(lat = as.numeric(lat_lon[,1]), 
                    lon = as.numeric(lat_lon[,2]), 
                    Z = Z))
}


make_lat_lon_grid <- function(latStart, lonStart, grid_extent_padding, 
                              grid_resolution) {
  
  #lat is northing
  northingSequence <- seq(params$regionArea$latStart - grid_extent_padding, 
                          params$regionArea$latStart + params$regionArea$latSize + grid_extent_padding, 
                          by = grid_resolution)
  
  #lon is eating
  eastingSequence <- seq(params$regionArea$lonStart - grid_extent_padding, 
                         params$regionArea$lonStart + params$regionArea$lonSize + grid_extent_padding,
                         by = grid_resolution)
  
  pointGrid <- expand.grid(northing = northingSequence,
                           easting = eastingSequence)
  
  return(pointGrid)
}

makeSPointsForGMheights <- function(latStart, 
                                    lonStart, 
                                    grid_extent_padding, 
                                    grid_resolution, 
                                    CRSstring, 
                                    CRSstring_GM) {
  
  pointGrid_GE <- make_lat_lon_grid(latStart = latStart, 
                                    lonStart = lonStart, 
                                    grid_extent_padding = grid_extent_padding, 
                                    grid_resolution = grid_resolution)
  
  pointGrid_sp <- SpatialPoints(pointGrid_GE[2:1], proj4string = CRS(CRSstring))
  
  pointGrid_sp_WGS84 <- spTransform(pointGrid_sp, CRS(CRSstring_GM))
  
  return(pointGrid_sp_WGS84)
}

GM_getAslRaster <- function(GMSPgrid, 
                            callPause_sec = 2,
                            CRSstring, 
                            CRSstring_GM = "+init=epsg:4326", 
                            maxCoordsPerCall = 400) {
  
  pointGrid_df <- data.frame(GMSPgrid)
  seq_ind <- seq(1, nrow(pointGrid_df), by = maxCoordsPerCall)
  #preallocate
  oMat <- matrix(nrow = nrow(pointGrid_df), ncol = 3)
  for (i in 1:length(seq_ind)) {
    from <- seq_ind[i]
    if (i == length(seq_ind)) {
      to <- nrow(pointGrid_df)
    } else {
      to <- seq_ind[i + 1]
    }
    ind <- from:to
    iter_vals <- GM_aslheight_api_call_chunk(pointGrid_df[ind,][2:1])
    oMat[ind, ] <- as.matrix(GM_format_api_result(iter_vals))
    if (i > 1) Sys.sleep(callPause_sec)
  }
  
  pointGrid_df_z <- SpatialPointsDataFrame(data.frame(oMat[,2:1]),
                                           data.frame("Z" = oMat[,3]), 
                                           proj4string = CRS(CRSstring_GM))
  
  pointGrid_sp_UTM <- spTransform(pointGrid_df_z, CRS(CRSstring))
  
  raster_z <- raster()
  extent(raster_z) <- extent(pointGrid_sp_UTM)
  res(raster_z) <- rep(gridResolution_GM * 1.1, 2)
  raster_z <- raster::rasterize(pointGrid_sp_UTM, raster_z, field = "Z")
  raster_z_interp <- raster::disaggregate(raster_z, 
                                          fact = res(raster_z) / rasterRes_final, 
                                          method = 'bilinear')
  
  if (any(is.na(raster_z_interp[]))) {
    stop("Missing GM heights: coarsen raster resolution [rasterRes_final]")
  } 
  
  return(raster_z_interp)
}

getASLraster <- function(latStart, 
                         lonStart,
                         grid_extent_padding, 
                         grid_resolution,
                         CRSstring, 
                         CRSstring_GM = "+init=epsg:4326") {
  
  SPpointsGM <- makeSPointsForGMheights(latStart, 
                                        lonStart,
                                        grid_extent_padding, 
                                        grid_resolution,
                                        CRSstring, 
                                        CRSstring_GM)
  
  raster_z_interp <- GM_getAslRaster(SPpointsGM, 
                                     CRSstring = params$projection)
  
  return(raster_z_interp)
  
}
