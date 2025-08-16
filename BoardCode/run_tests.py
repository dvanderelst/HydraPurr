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
TESTS = [7]

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
                print("Test 1: Switching feeder relay (3 cycles, 0.5s each).")
                for i in range(3):
                    print(f" Relay cycle {i+1} → ON")
                    hp.feeder_on()
                    time.sleep(0.5)
                    print(" Relay → OFF")
                    hp.feeder_off()
                    time.sleep(0.5)
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
                    value = hp.read_water_level(samples=50, dt=0.001)  # matches HydraPurr wrapper  :contentReference[oaicite:1]{index=1}
                    print(f" Reading {i+1}: {value}")
                    time.sleep(1)
                print("Test 3 completed.")

            elif test == 4:
                # Bluetooth send
                print("Test 4: Bluetooth send (10 messages).")
                for i in range(10):
                    msg = f"Sending {i}"
                    print(f" BT → {msg}")
                    hp.bluetooth_send(msg)
                    time.sleep(0.25)
                print("Test 4 completed.")

            elif test == 5:
                # Lick detection (ADC channel 1 on HydraPurr)
                print("Test 5: Lick detection (50 reads).")
                for i in range(50):
                    value = hp.read_lick()
                    print(f" Lick {i+1}: {value}")
                    time.sleep(0.5)
                print("Test 5 completed.")

            elif test == 6:
                # SD logging via MyStore through HydraPurr
                print("Test 6: SD logging (erase + write a few lines, then read).")
                fname = "hydra_test.csv"
                hp.create_log(fname)
                # Erase file (re-create) by calling MyStore.erase() through the stored instance
                hp.stores[fname].erase()  # MyStore exposes erase()  :contentReference[oaicite:2]{index=2}
                hp.log(fname, ['one', 1, 2, 3])
                hp.log(fname, ['two', 4, 5, 6])
                hp.log(fname, ['three', 7, 8, 9])
                print(" Wrote 3 rows. Reading back:")
                rows = hp.read_log(fname, split=True)
                print(" ", rows)
                print("Test 6 completed.")

            elif test == 7:
                # RTC set/get
                print("Test 7: Setting RTC (keep date, set minute to 30, seconds to 0), then read.")
                # Partial set: only update some fields (HydraPurr handles keeping others)  :contentReference[oaicite:3]{index=3}
                hp.set_time(mn=30, sc=0)
                print(" Current time (string):", hp.get_time(as_string=True))
                print(" Current time (dict):", hp.get_time(as_string=False))
                print("Test 7 completed.")

            elif test == 8:
                # RFID read (limited attempts)
                print("Test 8: RFID read (5 attempts).")
                for i in range(5):
                    data = hp.read_rfid()
                    if data is None:
                        print(" No valid package.")
                    else:
                        print(" Interpreted:", data)
                    time.sleep(2)
                print("Test 8 completed.")

            else:
                print(f"Unknown test id: {test}")

        except Exception as e:
            # Keep the loop going even if a device is missing
            print(f"[ERROR] Test {test} raised: {e}")

        time.sleep(2)
        print(f"=== Finished Test {test} ===")

if __name__ == "__main__":
    main()
