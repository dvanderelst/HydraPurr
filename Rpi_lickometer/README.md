# Installing the library on Raspberry Pi

1. Make sure the required python libraries are installed. You can install the libraries from the command line on the raspberry pi. Execute the following lines at the command lines (one by one):

```bash
pip3 install adafruit-blinka
pip3 install adafruit-circuitpython-mcp3xxx
pip3 install pillow
pip3 install adafruit-circuitpython-ssd1306
```

2. Download the library from this repository (Click the green `code` button and select `download as zip`).
3. Unzip the downloaded file and copy the resulting folder to the Raspberry  Pi. You should now be able to run any of  the test scripts in the folder (`run_test_xxx.py`) or write your own code using the `LickLibrary` library.