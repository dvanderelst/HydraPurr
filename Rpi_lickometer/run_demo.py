# SET THE LICK SWITCH TO ANALOG

import time
from LickLibrary import Control
from LickLibrary import myOLED
from LickLibrary import Control
from LickLibrary import myKeypad

use_analog = True
threshold = 10000
required_licks = 3


keypad = myKeypad.myKeypad()
detector = Control.LickDetector(analog=use_analog)
oled = myOLED.myOLED(flipped=True)
feeder = Control.Feeder()
feeder.off()
nr_licks = 0

while True:
    data = detector.get_lick()
    key = keypad.get_key()
    print(data, key)
    if key == 'A': nr_licks = 10000
    if data > threshold:
        nr_licks = nr_licks + 1
        oled.set_text(0, 'Lick detected')
        oled.set_text(1, 'Good kitty!')
        oled.set_text(2, str(nr_licks))
        while data > threshold:
            data = detector.get_lick()
            time.sleep(0.1)
    else:
        oled.set_text(0, 'Waiting for lick')
        oled.set_text(1, '')
        oled.set_text(2, '')
    if nr_licks >= required_licks:
        oled.set_text(2, 'Feeding Time!')
        nr_licks = 0
        feeder.on()
        time.sleep(3)
        feeder.off()





    # if data > threshold:
    #
    #     licked = True
    #     feeder.on()
    #     time.sleep(5)
    #     feeder.off()
    #
    # else:
    #     oled.set_text(0, 'No Lick detected')
    #     oled.set_text(1, '')
    #     licked = False
    #
    #
    # time.sleep(.5)
    # print(data)
    # #
    # oled.set_text(0, 'test line 1')
    # oled.set_text(1, 'test line 2')
