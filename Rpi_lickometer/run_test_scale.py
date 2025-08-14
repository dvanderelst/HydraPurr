from LickLibrary import myScales
import time

scale = myScales.myScale(scale_id='lick')

#scales.calibrate(scale_nr=2)
#scales.calibrate(scale_nr=2)

while True:
    r = scale.measure()
    print(r)
    time.sleep(0.5)