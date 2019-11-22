$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Push-Location $dir

[void][Reflection.Assembly]::LoadWithPartialName('Microsoft.VisualBasic')

$title = 'New simulation'
$msg   = 'Choose simulation name:'

$text = ""

$text = [Microsoft.VisualBasic.Interaction]::InputBox($msg, $title)

if($text.length -eq 0){
	$wshell = New-Object -ComObject Wscript.Shell
	$wshell.Popup("No simulation name defined. Quitting", 0, "Error", 0x1)
  exit
}

if(Test-Path "simulations\$($text)"){
	$wshell = New-Object -ComObject Wscript.Shell
	$wshell.Popup("Directory exists. Quitting", 0, "Error", 0x1)
	exit
}

New-Item "simulations\$($text)" -type directory

Copy-Item -recurse "baseFiles\*" "simulations\$($text)\"
$wshell = New-Object -ComObject Wscript.Shell

$wshell.Popup("Now run the programs within simulations\$($text)
Please refer to http://urban-climate.net/wiki/Google_Earth_3D_Modelling for details", 0, "Done", 0x1)

