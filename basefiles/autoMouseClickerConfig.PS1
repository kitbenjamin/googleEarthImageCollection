if (Get-Module -ListAvailable -Name powershell-yaml) {
    Write-Host "powershell-yaml already installed"
} 
else {
    Write-Host "powershell-yaml must be installed using: Install-Module powershell-yaml -Scope CurrentUser"
	Read-Host "Press enter to exit..."
	exit
}

$wshell = New-Object -ComObject Wscript.Shell

$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Push-Location $dir

[string[]]$fileContent = Get-Content "metaData/imageCollectionConfig.yml"
$content = ''
foreach ($line in $fileContent) { $content = $content + "`n" + $line }
$yaml = ConvertFrom-YAML $content

if(!$yaml['autoMouseClicker']['useAutoMouseClicker']){
 $wshell.Popup('Please set `useAutoMouseClicker` to `True` in imageCollectionConfig.yml')
 exit(0)
}

$text = $wshell.Popup(
' CLOSE GOOGEL EARTH AND ANY MOUSE CLICKING SOFTWARE. Then follow these steps after you hit OK:
 1) Check Google Earth has auto loaded. Keep Google Earth maximised.
 2) Mouse click record will also open. Start recording mouse (F9).
 3) Click through GE to start the tour as normal (pause,rewind then close [cross] the currently playing tour -> Tools -> Movie Maker -> Select `a saved tour:` -> Create Movie)
 4) Stop recording mouse (F10)
 5) Save the recording as: metaData/mouseMacro/mouse_macro.mcs or as defined in the params yaml `macroFileName`
 6) Check the macro runs OK
 7) Clear the output images from the testing, once happy')

$GEexe = $yaml['scriptDirectories']['googleEarthDir'] + "googleearth.exe"

$AMCrec = $yaml['autoMouseClicker']['progFullDir'] + "\Recorder\MouseClickRecorder.exe"

$AMCrun = $yaml['autoMouseClicker']['progFullDir'] + "\AmcEngine.exe"

$AMCfile = $yaml['autoMouseClicker']['macroFileName']
$AMCfileFull = $dir + "\" + $AMCfile

$sampleTour=$dir + "\metaData\mouseMacro\sample_tour.kml"

Start-Process $AMCrec
Start-Process $GEexe -WindowStyle maximized -ArgumentList $sampleTour  -Wait

$wshell.Popup('After you hit OK, Google Earth will open. After 15 s the macro will run.')
sleep 0.5
Start-Process $GEexe -WindowStyle maximized -ArgumentList $sampleTour
sleep 15
Start-Process $AMCrun -ArgumentList $AMCfileFull
