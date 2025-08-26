import board

from components import MyDigital
from components import MyOLED
from components import MyADC
from components import MyBT
from components import MyStore
from components import MyRTC
from components import MyRFID

from components.MySystemLog import debug, info, warn, error
from components.MyStore import print_directory

class HydraPurr:
    def __init__(self):
        # Defines the built-in LED
        self.indicator = MyDigital(pin=board.D25, direction="output")
        # Defines the relay that controls the feeder
        self.feeder = MyDigital(pin=board.D6, direction='output')
        # Defines the OLED screen
        self.screen = MyOLED()
        self.screen.set_rotation(False)
        # Defines the water level sensor
        self.water_level = MyADC(0)
        # Defines the Bluetooth hardware module
        self.bluetooth = MyBT()
        # Defines the lick sensor
        self.lick = MyADC(1)
        self.lick_threshold = 2.0
        # Storing the storage files
        self.stores = {}
        # Defines the RTC for timekeeping
        self.rtc = MyRTC()
        # Defines the RFID reader
        #self.rfid_reader = MyRFID() -- > Should not be part of this class.
        # Set up logging for this class
        debug("[HydraPurr] HydraPurr initialized")

    # --- read lick ---
    def read_lick(self, binary=True):
        lick_value = self.lick.read()
        lick_threshold = self.lick_threshold
        if binary: lick_value = 1 if lick_value < lick_threshold else 0
        debug(f'[HydraPurr] Lick value: {lick_value}, binary: {binary}')
        return lick_value

    # --- indicator LED control ---
    def indicator_on(self):
        self.indicator.write(True)
        debug('[HydraPurr] Indicator LED on')

    def indicator_off(self):
        self.indicator.write(False)
        debug('[HydraPurr] Indicator LED off')

    def indicator_toggle(self):
        self.indicator.toggle()
        debug('[HydraPurr] Indicator LED toggle')

    # --- feeder relay control ---
    def feeder_on(self):
        self.feeder.write(True)
        debug('[HydraPurr] Feeder on')

    def feeder_off(self):
        self.feeder.write(False)
        debug('[HydraPurr] Feeder off')

    def feeder_toggle(self):
        self.feeder.toggle()
        debug('[HydraPurr] Feeder toggle')

    # --- screen ---
    def screen_write(self, text, x=0, y=0, scale=None, clear=True):
        self.screen.write(text, x, y, scale=scale, clear=clear)
        debug(f'[HydraPurr] Screen write: {text}')

    # --- water level ---
    def read_water_level(self, samples=50, dt=0.001):
        water_value = self.water_level.mean(num_samples=samples, sample_delay=dt)
        debug(f'[HydraPurr] Water level value: {water_value}')
        return water_value

    # --- send bt data ---
    def bluetooth_send(self, message):
        message = str(message)
        self.bluetooth.send(message)
        debug(f'[HydraPurr] Bluetooth send: {message}')

    # --- RTC time ---
    def set_time(self, yr=None, mt=None, dy=None, hr=None, mn=None, sc=None):
        self.rtc.set_time(yr, mt, dy, hr, mn, sc)
        debug(f'[HydraPurr] Set time {(yr,mt,dy,hr,mn,sc)}')

    def get_time(self, as_string=False):
        return self.rtc.get_time(as_string=as_string, with_seconds=True)

    # --- read rfid ---
    def read_rfid(self):
        data_package = self.rfid_reader.read_data_package()
        if data_package:
            interpreted_data = self.rfid_reader.interpret_data_package(data_package)
            return interpreted_data
        return None

    # --- data logging ---
    def create_data_log(self, filename): #alias for ease
        return self.select_data_log(filename)
    
    def select_data_log(self, filename):
        exists = filename in self.stores
        if not exists: self.stores[filename] = MyStore(filename)
        selected_storage = self.stores[filename]
        return selected_storage

    def add_data(self, filename, data):
        selected_storage = self.select_data_log(filename)
        result = selected_storage.add(data)
        return result

    def read_data_log(self, filename):
        selected_storage = self.select_data_log(filename)
        return selected_storage.read()
    
    def empty_data_log(self, filename):
        selected_storage = self.select_data_log(filename)
        selected_storage.empty()
        return selected_storage

    @staticmethod
    def print_directory(): # alias for ease
        print_directory('/sd')
        
        
        
