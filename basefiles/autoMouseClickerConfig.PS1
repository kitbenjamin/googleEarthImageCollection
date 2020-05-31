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
' CLOSE GOOGLE EARTH (GE) AND ANY MOUSE CLICKING SOFTWARE. Then follow these steps after you hit OK (this window closes when you hit OK):
 1) Check GE has auto loaded. Keep GE maximised.
 2) Mouse click record will also open. Tick `on top` and make sure window is out of the way of any important GE GUI. Start recording mouse.
 3) Click through GE to start the tour as normal (pause,rewind then close [cross] the currently playing tour -> Tools -> Movie Maker -> Select `a saved tour:` -> Create Movie)
 4) Stop recording mouse
 5) Save the macro (file -> save as as: metaData/mouseMacro/mouse_macro.mmmacro or as defined in the params yaml `macroFileName`
 6) Close GE
 7) Follow the popup window steps to check the macro runs OK. The macros should run some time after GE is started.
 8) Stop GE recording and close GE as you wish
 9) Clear the output images from the testing, once happy')

$GEexe = $yaml['scriptDirectories']['googleEarthDir'] + "googleearth.exe"

$AMC = $yaml['autoMouseClicker']['progFullDir']

$AMCfile = $yaml['autoMouseClicker']['macroFileName']
$AMCfileFull = $dir + "\" + $AMCfile

$sampleTour=$dir + "\metaData\mouseMacro\sample_tour.kml"

Start-Process $AMC
Start-Process $GEexe -WindowStyle maximized -ArgumentList $sampleTour  -Wait

$wshell.Popup('Now checking it works. After you hit OK, Google Earth will open. Don`t interact with GE: let the tour run. After 20 s the macro you just made to save the tour images should run. You can then close GE as you please.')
sleep 0.5
Start-Process $GEexe -WindowStyle maximized -ArgumentList $sampleTour
sleep 20
Start-Process $AMC -ArgumentList $AMCfileFull
