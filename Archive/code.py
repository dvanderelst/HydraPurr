import myADC
import myPixel
import myDigital
import myBT
import myOLED
import myRTC
import time
import board

import test_rfid

# current_time = myRTC.data_time_str()
# print('current date and time:', current_time)
# 
# blue_led = myDigital.myDigital(board.D25, 'output')
# water_level = myADC.myADC(0)
# pixel = myPixel.myPixel(brightness = 0.1)
# feeder = myDigital.myDigital(board.D6, 'output')
# lick = myDigital.myDigital(board.D5, 'input', 'up')
# oled = myOLED.myOLED()
# bt = myBT.myBT()
# 
# while True:
#     feeder.write(False)
#     pixel.set_color('green')
#     blue_led.write(1)
#     value = water_level.mean()
#     lick_value = lick.read()
#     
#     bt.send(f'{value}, {lick_value}')
#     print(value, lick_value)
#     text_value = int(value * 1000)
#     current_time = myRTC.time_str()
#     
#     oled.write(text_value, 5, 0, scale=2)
#     oled.write(current_time, 5, 20, scale=1, clear=False)
#     
#     pixel.set_color('blue')
#     blue_led.write(0)
#     feeder.write(True)
#     time.sleep(0.5)
# 


