# RP2040 HydraPurr

+ The BoardCode folder can be kept in sync with the board contents using my very own `DeviceSync` script: `/home/dieter/Dropbox/PythonRepos/DeviceSync`
+ The `BoardCode` folder is an independent Pycharm Project to avoid issues when using refactoring. If ever want to develop other code (code not running on the board) in this folder, I should probably put that inside a new folder, as a different pyCharm project, for the same reason. For example:

````
RP2040_HydraPurr
|
|___ BoardCode = a pyCharm project
|
|___ Other_part_of_the_HydraPurr codebase = a pyCharm project

````