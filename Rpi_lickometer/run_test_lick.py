import time
from LickLibrary import Control

use_analog = True

detector = Control.LickDetector(analog=use_analog)

for i in range(1000):
    data = detector.get_lick()
    print(data)
    time.sleep(.5)

