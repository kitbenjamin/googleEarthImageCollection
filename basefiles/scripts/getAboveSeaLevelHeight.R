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

multipleRawHeightAboveSeaLevelHeightFromGoogleAPI <- function(twoDlatlons, return.call = "json", 
                                                      apiKey = "AIzaSyDiklf_BgSg67hfNzrJXEWeNcgrOXQzRGY",
                                                      verbose = FALSE){
  suppressWarnings(suppressMessages(require(RCurl)))
  suppressWarnings(suppressMessages(require(RJSONIO)))
  pasted = apply(twoDlatlons, 1, function(x){paste0(x[1], ',', x[2])})
  toSubmit = paste0(pasted, collapse = '|')
  #get *single* height above sea level [has capability of multiple returns but CBA]
  root <- "https://maps.googleapis.com/maps/api/elevation/"
  address <- paste(root, return.call, "?locations=", toSubmit, "&key=",apiKey, sep = "")
  if(verbose) print(address)
  doc <- getURL(address)
  x <- fromJSON(doc,simplify = FALSE)
  if (x$status != "OK") stop("apiKey error")
  return(x)
}

multipleFormatHeightAboveSeaLevelHeightFromGoogleAPI <- function(heightJSON){
  formatted <- lapply(heightJSON[[1]], function(y){c("lat" = y$location$lat, "lon" = y$location$lng, "elevation" = y$elevation)})
  return(formatted)
}

getMultipleHeightAboveSeaLevelFromGoogleAPI <- function(twoDlatlons, return.call = "json", 
                                                apiKey = "AIzaSyDiklf_BgSg67hfNzrJXEWeNcgrOXQzRGY",
                                                verbose = FALSE){
  
  heightJSON <- multipleRawHeightAboveSeaLevelHeightFromGoogleAPI(twoDlatlons)
  return(multipleFormatHeightAboveSeaLevelHeightFromGoogleAPI(heightJSON))
}
