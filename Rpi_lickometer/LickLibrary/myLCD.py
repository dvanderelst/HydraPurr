import board
import busio
import time

import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd

red = [100, 0, 0]
green = [0, 100, 0]
blue = [0, 0, 100]


class MyLCD:
    def __init__(self):
        self.lcd_columns = 16
        self.lcd_rows = 2
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.lcd = character_lcd.Character_LCD_RGB_I2C(self.i2c, self.lcd_columns, self.lcd_rows)
        self.message = None

    def set_color(self, color_name):
        if color_name == 'red': self.lcd.color = red
        if color_name == 'green': self.lcd.color = green
        if color_name == 'blue': self.lcd.color = blue

    def blink_cursor(self, state):
        self.lcd.blink = state

    def set_text(self, line1='',line2=''):
        line1 = str(line1)
        line2 = str(line2)
        max_length = len(line1)
        if len(line2) > max_length: max_length = len(line2)
        over_length = max_length - self.lcd_columns
        if over_length < 0: over_length = 0
        message = line1 + '\n' + line2
        if message != self.message: self.lcd.clear()
        self.message = message
        self.lcd.message = message
        for i in range(over_length):
            time.sleep(0.25)
            self.lcd.move_left()

    @property
    def left(self):
        return self.lcd.left_button

    @property
    def right(self):
        return self.lcd.right_button

    @property
    def up(self):
        return self.lcd.up_button

    @property
    def down(self):
        return self.lcd.down_button

    @property
    def select(self):
        return self.lcd.select_button

    def get_buttons(self):
        left = self.left
        right = self.right
        up = self.up
        down = self.down
        select = self.select
        return [left, right, up, down, select]






  # if lcd.left_button:
  #       print("Left!")
  #       lcd.message = "Left!"
  #
  #   elif lcd.up_button:
  #       print("Up!")
  #       lcd.message = "Up!"
  #
  #   elif lcd.down_button:
  #       print("Down!")
  #       lcd.message = "Down!"
  #
  #   elif lcd.right_button:
  #       print("Right!")
  #       lcd.message = "Right!"
  #
  #   elif lcd.select_button:
  #       print("Select!")
  #       lcd.message = "Select!"