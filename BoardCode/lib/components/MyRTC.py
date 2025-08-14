import time
import board
import busio
import adafruit_pcf8523

class MyRTC:
    def __init__(self):
        # Use fixed pins (board.SCL, board.SDA)
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.rtc = adafruit_pcf8523.PCF8523(self.i2c)

    # ---- reads ----
    def now(self):
        """Return time.struct_time from the RTC."""
        return self.rtc.datetime

    def date_str(self):
        """Return 'Weekday d/m/yyyy'."""
        t = self.now()
        #todo: Check whether this is the correct order for tm_wday
        days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
        return f"{days[t.tm_wday]} {t.tm_mday}/{t.tm_mon}/{t.tm_year}"

    def time_str(self, with_seconds=True):
        """Return 'hh:mm' or 'hh:mm:ss'."""
        t = self.now()
        if with_seconds:
            return f"{t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}"
        return f"{t.tm_hour:02d}:{t.tm_min:02d}"

    def datetime_str(self, with_seconds=True):
        """Return 'Weekday d/m/yyyy hh:mm[:ss]'."""
        return f"{self.date_str()} {self.time_str(with_seconds)}"

    # ---- writes ----
    def set_datetime(self, year, month, day, hour, minute, second, weekday=None):
        """
        Set the RTC. weekday: 0=Mon .. 6=Sun (PCF8523 accepts 0-6; Python struct_time uses 0=Mon).
        If weekday=None, it’s computed automatically.
        """
        if weekday is None:
            tmp = time.struct_time((year, month, day, hour, minute, second, 0, 0, -1))
            weekday = time.localtime(time.mktime(tmp)).tm_wday

        t = time.struct_time((year, month, day, hour, minute, second, weekday, -1, -1))
        self.rtc.datetime = t

    def set_from_struct(self, t: time.struct_time):
        """Set RTC from an existing struct_time."""
        self.rtc.datetime = t

    def set_from_dict(self, d):
        """
        Set RTC from a dict:
        d = {'year':YYYY, 'month':M, 'date':D,
             'hours':h, 'minutes':m, 'seconds':s,
             'weekday':w (optional)}
        """
        self.set_datetime(
            d["year"], d["month"], d["date"],
            d["hours"], d["minutes"], d["seconds"],
            d.get("weekday", None)
        )
