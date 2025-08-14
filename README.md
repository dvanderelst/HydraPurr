# HydraPurr

+ The BoardCode folder can be kept in sync with the board contents using my very own `DeviceSync` script: `/home/dieter/Dropbox/PythonRepos/DeviceSync`
+ The `BoardCode` folder is an independent Pycharm Project to avoid issues when using refactoring. Other code (code not running on the board) in this folder, should be put inside a new folder, as a different PyCharm project, for the same reason. For example:

````
HydraPurr
|___ BoardCode = a Pycharm project
|___ FitWaterFunction = a Pycharm project
|___ Other_Code_Part = a Pycharm Project

````
