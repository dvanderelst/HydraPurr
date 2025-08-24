import busio
from library import adafruit_pcf8523
import time
import board

myI2C = busio.I2C(board.SCL, board.SDA)
rtc = adafruit_pcf8523.PCF8523(myI2C)

def get_time():
    t = rtc.datetime
    return t

def date_str():
    t = rtc.datetime
    days = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
    string = ("%s %d/%d/%d" % (days[t.tm_wday], t.tm_mday, t.tm_mon, t.tm_year))
    return string

def time_str():
    t = rtc.datetime
    string = ("%d:%02d:%02d" % (t.tm_hour, t.tm_min, t.tm_sec))
    return string

def data_time_str():
    time_string = time_str()
    date_string = date_str()
    total = date_string + ' ' + time_string
    return total

def set_time(structure):
    year = structure['year']
    month = structure['month']
    date = structure['date']
    
    hours = structure['hours']
    minutes = structure['minutes']
    seconds = structure['seconds']
    
    weekday = structure['weekday']
    
    t = time.struct_time((year,  month,   date,   hours,  minutes,  seconds,    weekday,   -1,    -1))
    print("Setting time")
    rtc.datetime = t
    string = data_time_str()
    print('Current date time string:', string)
