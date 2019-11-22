if (Get-Module -ListAvailable -Name powershell-yaml) {
    Write-Host "powershell-yaml already installed"
} 
else {
    Write-Host "powershell-yaml must be installed using: Install-Module powershell-yaml -Scope CurrentUser"
	Read-Host "Press any key to exit..."
	exit
}

$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Push-Location $dir

[string[]]$fileContent = Get-Content "metaData/imageCollectionConfig.yml"
$content = ''
foreach ($line in $fileContent) { $content = $content + "`n" + $line }
$yaml = ConvertFrom-YAML $content

$PyscriptLocstr = $yaml['scriptDirectories']['pythonDir']

$LOG = "LOG\LOG_preProcessing.txt"
if(![System.IO.File]::Exists($LOG)){
	New-Item $LOG -type file
}
Push-Location $dir
Remove-Item $LOG
Start-Transcript -path $LOG -append -Force
& "${PyscriptLocstr}/python.exe" "scripts/kmlCreator.py"
& "${PyscriptLocstr}/python.exe" "scripts/calcViewDomain.py"
Stop-Transcript
Pop-Location

Read-Host "Press any key to exit..."
exit