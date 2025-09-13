import Tests
import MainLoop
from components.MySystemLog import DEBUG, INFO, WARN, ERROR
import LickCounterMultiple
lcm = LickCounterMultiple.LickCounter(cat_names=['cat1', 'cat2', 'cat3'], clear_log=True)

# print('Running...')
# tests_to_run = []
# # Select which tests to run (same numbering as the old script)
# # 0 -> blinking indicator LED
# # 1 -> switching relay
# # 2 -> screen test
# # 3 -> water level reading
# # 4 -> Bluetooth module
# # 5 -> lick detection
# # 6 -> writing to SD (log file)
# # 7 -> set/get RTC time
# # 8 -> RFID module
# if len(tests_to_run) > 0: hp, log = Tests.main(tests_to_run)
# else: MainLoop.main_loop(level=INFO)