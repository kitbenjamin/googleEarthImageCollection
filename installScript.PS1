$scriptpath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptpath
Push-Location $dir

If(!(test-path "regions"))
{
      New-Item -ItemType Directory -Force -Path "regions"
}

[void][Reflection.Assembly]::LoadWithPartialName('Microsoft.VisualBasic')

$title = 'New region'
$msg   = 'Choose region name:'

$text = ""

$text = [Microsoft.VisualBasic.Interaction]::InputBox($msg, $title)

if($text.length -eq 0){
	$wshell = New-Object -ComObject Wscript.Shell
	$wshell.Popup("No region name defined. Quitting", 0, "Error", 0x1)
  exit
}

if(Test-Path "regions\$($text)"){
	$wshell = New-Object -ComObject Wscript.Shell
	$wshell.Popup("Directory exists. Quitting", 0, "Error", 0x1)
	exit
}

New-Item "regions\$($text)" -type directory

Copy-Item -recurse "baseFiles\*" "regions\$($text)\"
$wshell = New-Object -ComObject Wscript.Shell

$wshell.Popup("Now run the programs within regions\$($text)
Please refer to https://github.com/kitbenjamin/googleEarthImageCollection for details", 0, "Done", 0x1)

