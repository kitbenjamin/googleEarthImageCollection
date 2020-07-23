require(processx)
require(ps)

#read in the args defined in kmlCreator.py
args <- commandArgs(trailingOnly = TRUE)

GEexe <- args[1]
#print(paste('Google Earth location: ', GEexe))
kmlPath <-  args[2]
#print(paste('The KML file is: ', kmlPath))
timeout <- args[3]
#print(paste('Time google earth will run before timeout: ', timeout))
timeout <- as.numeric(timeout)

if (is.na(timeout)) stop("timeout is NA")

#Open google earth with kml file
print('Opening google earth')
p <- process$new(command = GEexe, kmlPath)
p_ps <- p$as_ps_handle()
PID <- ps::ps_pid(p_ps)
#print(paste("GE process ID is:", PID))
tStart <- Sys.time()
# loop until timeout reached
for (i in 1:(timeout * 2)) {
  Sys.sleep(0.5)
  tDiff_secs <- as.numeric(difftime(Sys.time(), tstart, units = "secs"))
  #test if crashed
  outRaw <- system(paste0("powershell -command (Get-Process -Id ", PID, ").Responding"), intern = TRUE)
  outBool <- ifelse(outRaw == "True", 1, 0)
  #check if been quit
  status <- system(paste0("powershell -command Get-Process -Id ", PID, " -ErrorAction SilentlyContinue"), intern = TRUE)
  #If user closed GE
  if (length(status) == 0) {
    print('Google earth ended')
    print(paste0('time since started:', tDiff_secs))
    endStatus = 'aborted'
    break
  #if crashed
  } else if (outRaw != "True") { 
    print('crash detected')
    print(paste('Google earth ended at ', Sys.time() ))
    endStatus = 'crashed'
    break
  #if timeout reached 
  } else if (tDiff_secs > timeout) {
    print('Timeout reached')
    endStatus = 'crashed'
    p$kill_tree()
    break
  } 
}

#give the end status that can be interpreted by kmlCreator.py
print(endStatus)

