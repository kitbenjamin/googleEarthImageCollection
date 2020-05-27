#get yaml config

#from yaml
$autoMouseClickerDir="C:\Program Files (x86)\Auto Mouse Clicker v10.1"

if yaml$useAutoMouseClicker== False: you have not set useAutoMouseClicker to True

if !file exists $autoMouseClickerDir\Recorder\MouseClickRecorder.exe stop

#look for existing recordings
#if recording found, print ("there is 1 recording that will be deleted")
#would you like to make new recording?
#if no, quit
#if yes
#dialog: the program will start. and GE will start with a dummy kml. 
#do the mouse recording to run a tour
#& $autoMouseClickerDir\Recorder\MouseClickRecorder.exe 



