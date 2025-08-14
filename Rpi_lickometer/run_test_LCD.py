from LickLibrary import myLCD
import time

display = myLCD.MyLCD()
display.set_color('green')

while True:
    if display.left: display.set_text('left')
    if display.right: display.set_text('right')
    if display.up: display.set_text('up')
    if display.down: display.set_text('down')
    if display.select: display.set_text('select')
    time.sleep(0.1)

