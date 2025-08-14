from LickLibrary import myKeypad
import time
keypad = myKeypad.myKeypad()


while True:
    key = keypad.get_key()
    #print(key)
    if key: print('key:', key)
    time.sleep(0.01)