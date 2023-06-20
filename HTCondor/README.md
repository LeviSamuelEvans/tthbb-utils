#### Quick info on how to run TRExSubmit.py

To run this script, you will need to house it in the same directory as the output and error directories. Currently, you will need to make the error and output directories, calling them what you would like and then put these names into the script. You can also name the submit directory what you would like, and the script will automatically make this directory. This directory houses all the .sh files and .sub files that the script makes to run the condor jobs. 

To run, simply do:
```
python TRExSubmit.py
```

------------

To split by region, you will want to set 
```
runRegsSep = True
```

And set the action to n for the histogram generation step

```
actions = 'n' 
```

You will need to set the path to the directory housing the trex configuration files, using :

```
configsDir = /path/to/configs
```

Then, you can set up as many configs as you would like to run over in :

```
listOfConfigs = [ configsDir + '<nameOfConfig>']
```

Note: You only want to run the `n` step splitting by regions, for workspace creation and fits you want to then set this to false.

In addition, you will need to set 
```
exePath = /path/to/TRExFitter/build/bin/trex-fitter
```
to be your own TRExFitter repository that you have cloned from https://gitlab.cern.ch/TRExStats/TRExFitter/

Plus, make sure in the `writeSubmit` function, to source the setup.sh script also from your own TRExFitter repo. 

As a final note, this script can definitely be improved, and is in development. 
