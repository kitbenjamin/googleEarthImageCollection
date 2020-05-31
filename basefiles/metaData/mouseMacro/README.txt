Non-exhaustive guide to getting GE to automatically restart the tour via a mouse clicking macro. In essence and with a bit of luck,
by setting the relevant yml parameter to "True", the mouse macro (MM) exe will run just before GE. 
The MM exe will use the yml parameter file name: *.mmacro. 

1) load GE via the metaData\mouseMacro\sample_tour.kml file (dbl. click the kml)
2) run tour maker with highest image setting and make it crash (~7000 x 4000 px)
3) run mini mouse macro (bin/MiniMouseMacro.exe)
4) repeat step 1
5) you should get GE pop up saying "GE crash detected". hit "record macro" on MiniMouseMacro.exe. 
6) run macro including all clicks required to get the tour running again.
7) save macro in metaData\, and set yml params accordingly (also set macro use to "True")
8) may need to manually edit the macro (it's a plain text file) to tweak the click timings.
