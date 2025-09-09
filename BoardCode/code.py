import Tests

# Select which tests to run (same numbering as the old script)
# 0 -> blinking indicator LED
# 1 -> switching relay
# 2 -> screen test
# 3 -> water level reading
# 4 -> Bluetooth module
# 5 -> lick detection
# 6 -> writing to SD (log file)
# 7 -> set/get RTC time
# 8 -> RFID module
tests_to_run = [5]
if len(tests_to_run) > 0: hp, log = Tests.main(tests_to_run)