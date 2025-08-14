import board

from components import MyDigital
from components import MyOLED
from components import MyADC
from components import MyBT
from components import MyStore
from components import MyRTC
from components import MyRFID

class HydraPurr:
    def __init__(self):
        # Defines the built-in LED
        self.indicator = MyDigital(pin=board.D13, direction="output")
        # Defines the relay that controls the feeder
        self.feeder = MyDigital(pin = board.D6, direction = 'output')
        # Defines the OLED screen
        self.screen = MyOLED()
        # Defines the water level sensor
        self.water_level = MyADC(0)
        # Defines the Bluetooth hardware module
        self.bluetooth = MyBT()
        # Defines the lick sensor
        self.lick = MyADC(1)
        # Storing the storage files
        self.stores = {}
        # Defines the RTC for timekeeping
        self.rtc = MyRTC()
        # Defines the RFID reader
        self.rfid_reader = MyRFID()

    # --- indicator LED control ---
    def indicator_on(self): self.indicator.write(True)
    def indicator_off(self): self.indicator.write(False)
    def indicator_toggle(self): self.indicator.toggle()

    # --- feeder relay control ---
    def feeder_on(self): self.feeder.write(True)
    def feeder_off(self): self.feeder.write(False)
    def feeder_toggle(self): self.feeder.toggle()

    # --- screen ---
    def screen_write(self, text, x=0, y=0, scale=None, clear=True):
        self.screen.write(text, x, y, scale=scale, clear=clear)

    # --- water level ---
    def read_water_level(self, samples=50, dt=0.001):
        return self.water_level.mean(num_samples=samples, sample_delay=dt)

    # Send data over Bluetooth
    def bluetooth_send(self, message):
        message = str(message)
        self.bluetooth.send(message)

    # Set and get the current time from the RTC

    def set_time(self, yr=None, mt=None, dy=None, hr=None, mn=None, sc=None):
        current = self.rtc.now()
        year = current.tm_year if yr is None else yr
        month = current.tm_mon if mt is None else mt
        day = current.tm_mday if dy is None else dy
        hour = current.tm_hour if hr is None else hr
        minute = current.tm_min if mn is None else mn
        second = current.tm_sec if sc is None else sc
        self.rtc.set_datetime(year, month, day, hour, minute, second)

    def get_time(self, as_string=False):
        if as_string: return self.rtc.datetime_str()
        t = self.rtc.now()
        return {
            "year": t.tm_year,
            "month": t.tm_mon,
            "day": t.tm_mday,
            "hour": t.tm_hour,
            "minute": t.tm_min,
            "second": t.tm_sec,
            "weekday": t.tm_wday,  # 0=Mon..6=Sun
        }

    # Reading the rfid tag
    def read_rfid(self):
        data_package = self.rfid_reader.read_data_package()
        if data_package:
            interpreted_data = self.rfid_reader.interpret_data_package(data_package)
            return interpreted_data
        return None

    # Read lick sensor value

    def read_lick(self):
        value = self.lick.read()
        return value

    # Methods for logging data

    def create_log (self, filename):
        exists = filename in self.stores
        if not exists: self.stores[filename] = MyStore(filename)

    def log(self, filename, data):
        self.create_log(filename)
        selected_storage = self.stores[filename]
        result = selected_storage.add(data)
        return result

    def read_log(self, filename, split=True):
        self.create_log(filename)
        return self.stores[filename].read(split=split)
