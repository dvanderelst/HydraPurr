import time
import Cats

from components.MySystemLog import setup, set_level, DEBUG, INFO, WARN, ERROR
from components.MySystemLog import clear_system_log
from components.MySystemLog import debug, info, warn, error
from components.MyPixel import MyPixel

from LickCounter import LickCounter
from TagReader import TagReader     # new non-blocking, scheduled-reset version
from HydraPurr import HydraPurr

def now_ms(): return int(time.monotonic() * 1000)

# ---------------- config ----------------
TAG_REQUIRED = True  # gatekeeper mode; False = logger mode
ALLOW_UNKNOWN = False  # allow unknown tags to open gate
HOLD_MS = 3000  # presence window after last RFID hit
LOCK_RELEASE_MS = 2000  # require quiet gap before switching cats
# ----------------------------------------

def main_loop(clear_log=True, level=DEBUG):
    # Set up logging as first oder of business
    setup(filename="system.log", autosync=True)
    if clear_log: clear_system_log()
    set_level(level)

    info("[Main Loop] Start")

    all_cat_names = Cats.get_all_names()
    info(f'[Main Loop] all defined cats: {all_cat_names}')
    # Hardware / objects
    reader = TagReader()          # resets are handled inside; poll() never sleeps
    hydrapurr = HydraPurr()
    pixel = MyPixel()
    counter = LickCounter(cat_names=all_cat_names, clear_log=clear_log)

    # pixel control
    pixel.toggle_colors = ['red', 'green', 'blue']
    last_pixel_toggle = now_ms()
    # Presence/attribution state
    previous_lick_state_string = None
    previous_active_cat = None


    while True:
        current_time = now_ms()
        if current_time - last_pixel_toggle > 500:
            pixel.cycle()
            last_pixel_toggle = current_time

        # --- RFID reader (non-blocking) --------------------------------------
        pkt = reader.poll()
        if pkt is None: pkt = {}
        tag_key = pkt.get("tag_key", None)
        current_cat = Cats.get_name(tag_key)
        if current_cat != previous_active_cat:
            info('New cat detected: ' + str(current_cat))
            previous_active_cat = current_cat
        # lick_state = 1 if hydrapurr.read_lick(binary=True) else 0
        #
        # counter.set_active_cat(name)
        # counter.update(lick_state)
        # current_lick_state_string = counter.get_state_string()
        # if current_lick_state_string != previous_lick_state_string:
        #     print(current_lick_state_string)
        #     previous_lick_state_string = current_lick_state_string


