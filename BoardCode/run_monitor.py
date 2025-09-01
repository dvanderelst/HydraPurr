import time

import Cats

from components.MySystemLog import setup, set_level, DEBUG, INFO, WARN, ERROR
from components.MySystemLog import clear_system_log
from components.MySystemLog import debug, info, warn, error

from LickCounter import LickCounter
from TagReader import TagReader
from HydraPurr import HydraPurr


# Get all cats
all_cat_names = Cats.get_all_names()

# Set up logging
setup(filename="system.log", autosync=True)
clear_system_log()
set_level(WARN)
info("[Run Tests] Start")

# Set up tagread, hydrapurr and the lickcounters
lickcounters = {}
reader = TagReader()
hydrapurr = HydraPurr()
for name in all_cat_names: lickcounters[name] = LickCounter(name = name)


# Timing for tag reader (in ms)
tagreader_period = int(1000 / 3)
next_tagreader_reset = int(time.monotonic() * 1000)


info(f'[Monitor] all defined cats: {all_cat_names}')


last_hit = None
last_name = None

previous_ctr_state = None

while True:
    now_ms = int(time.monotonic() * 1000)
    if now_ms >= next_tagreader_reset:
        packet = reader.poll(reset_after=True)
        next_tagreader_reset += tagreader_period 
        if packet:
            last_hit = time.monotonic()
            last_tag = packet['tag']
            last_name = Cats.get_name(last_tag)
            info(f"[Monitor] Activating {last_name}")
    
        
    lick_state = hydrapurr.read_lick(binary=True)
    
    if last_name is not None:
        ctr = lickcounters[last_name]
        ctr.process_sample(lick_state)
        current_ctr_state = ctr.get_state()
        if previous_ctr_state != current_ctr_state:
            print(current_ctr_state)
            previous_ctr_state = current_ctr_state



