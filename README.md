# HydraPurr

## Organization Notes

+ The BoardCode folder can be kept in sync with the board contents using my very own `DeviceSync` script: `/home/dieter/Dropbox/PythonRepos/DeviceSync`
+ The `BoardCode` folder is an independent Pycharm Project to avoid issues when using refactoring. Other code (code not running on the board) in this folder, should be put inside a new folder, as a different PyCharm project, for the same reason. For example:

````
HydraPurr
|___ BoardCode = a Pycharm project
|___ FitWaterFunction = a Pycharm project
|___ Other_Code_Part = a Pycharm Project

````

+ Thursday, 14. August 2025 09:43AM. The code for the (older) Raspberry Pi version of the HydraPurr is still available as a GitHub repository:
`https://github.com/habit-tech/Rpi_lickometer`. However, I have  added the local code to this HydraPurr code by way of archiving it. It is unlikely we will develop the Raspberry Pi version further at this point but the Raspberry Pi code might be a good reference for developing some things on the Rp2040.