from LickLibrary import myKeypad
import time
keypad = myKeypad.myKeypad()
from LickLibrary import myOLED

oled = myOLED.myOLED()
counter = 0


while True:
    key = keypad.get_key()
    time.sleep(0.01)
    oled.set_text(0, counter)
    if key:
        print('key:', key)
        oled.set_text(1, key)
    counter = counter + 1