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
                                        verbose = FALSE){
  suppressWarnings(suppressMessages(require(RCurl)))
  suppressWarnings(suppressMessages(require(RJSONIO)))
  pasted <- apply(twoDlatlons, 1, function(x){paste0(x[1], ',', x[2])})
  toSubmit <- paste0(pasted, collapse = '|')
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

