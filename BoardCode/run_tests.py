# run_hydra_tests.py
# Tests the hardware via the HydraPurr facade, mirroring the old run_tests.py set.

import time
from HydraPurr import HydraPurr  # HydraPurr lives at project root  :contentReference[oaicite:0]{index=0}

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
TESTS = [0, 1, 2, 3, 4, 5, 6, 7, 8]

def main():
    hp = HydraPurr()

    for test in TESTS:
        print(f"\n=== Starting Test {test} ===")
        time.sleep(1)

        try:
            if test == 0:
                # Blink the indicator LED
                print("Test 0: Blinking the indicator LED (20 blinks).")
                for i in range(20):
                    hp.indicator_on()
                    time.sleep(0.1)
                    hp.indicator_off()
                    time.sleep(0.1)
                print("Test 0 completed.")

            elif test == 1:
                # Switch the feeder relay on/off
                print("Test 1: Switching feeder relay (3 cycles, 3s each).")
                for i in range(3):
                    print(f" Relay cycle {i+1} → ON")
                    hp.feeder_on()
                    time.sleep(3)
                    print(" Relay → OFF")
                    hp.feeder_off()
                    time.sleep(3)
                print("Test 1 completed.")

            elif test == 2:
                # Screen test
                print("Test 2: Writing numbers 0..9 to OLED.")
                for x in range(10):
                    hp.screen_write(str(x), x=5, y=0, scale=2, clear=True)
                    time.sleep(1)
                print("Test 2 completed.")

            elif test == 3:
                # Water level reading (ADC channel 0 on HydraPurr)
                print("Test 3: Water level (10 reads, mean over 50 samples).")
                for i in range(10):
                    value = hp
