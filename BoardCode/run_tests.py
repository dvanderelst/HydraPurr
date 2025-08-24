# run_hydra_tests.py
# Tests the hardware via the HydraPurr facade, mirroring the old run_tests.py set.

import time
from HydraPurr import HydraPurr  # HydraPurr lives at project root  :contentReference[oaicite:0]{index=0}
from components.MySystemLog import setup, set_level, DEBUG, INFO, info
from components.MySystemLog import clear_system_log, tail_to_console


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
TESTS = [6]


setup(filename="system.log", autosync=True)
clear_system_log()
set_level(DEBUG)
info("[Run Tests] Start")

def main():
    hp = HydraPurr()

    for test in TESTS:
        print(f"\n=== Starting Test {test} ===")
        time.sleep(1)

        try:
            if test == 0:
                # Blink the indicator LED
                info("Test 0: Blinking the indicator LED (20 blinks).")
                for i in range(20):
                    hp.indicator_on()
                    time.sleep(0.1)
                    hp.indicator_off()
                    time.sleep(0.1)
                print("Test 0 completed.")

            elif test == 1:
                # Switch the feeder relay on/off
                info("Test 1: Switching feeder relay (3 cycles, 0.5s each).")
                for i in range(3):
                    hp.feeder_on()
                    time.sleep(0.5)
                    hp.feeder_off()
                    time.sleep(0.5)
                print("Test 1 completed.")

            elif test == 2:
                # Screen test
                info("Test 2: Writing numbers 0..9 to OLED.")
                for x in range(10):
                    hp.screen_write(str(x), x=5, y=0, scale=2, clear=True)
                    time.sleep(1)
                print("Test 2 completed.")

            elif test == 3:
                # Water level reading (ADC channel 0 on HydraPurr)
                info("Test 3: Water level (10 reads, mean over 50 samples).")
                for i in range(10):
                    hp.read_water_level(samples=50, dt=0.001)  # matches HydraPurr wrapper  :contentReference[oaicite:1]{index=1}
                    time.sleep(1)
                print("Test 3 completed.")

            elif test == 4:
                # Bluetooth send
                info("Test 4: Bluetooth send (10 messages).")
                for i in range(10):
                    msg = f"Sending {i}"
                    hp.bluetooth_send(msg)
                    time.sleep(0.25)
                print("Test 4 completed.")

            elif test == 5:
                # Lick detection (ADC channel 1 on HydraPurr)
                info("Test 5: Lick detection (50 reads).")
                for i in range(50):
                    hp.read_lick()
                    time.sleep(0.5)
                print("Test 5 completed.")

            elif test == 6:
                # SD logging via MyStore through HydraPurr
                info("Test 6: SD logging (erase + write a few lines, then read).")
                fname1 = "hydra_test1.csv"
                fname2 = "hydra_test2.csv"
                hp.create_data_log(fname1)
                hp.create_data_log(fname2)
                
                hp.empty_data_log(fname1)
                hp.empty_data_log(fname2)
                   
                hp.add_data(fname1, ['one', 1, 2, 3])
                hp.add_data(fname1, ['two', 4, 5, 6])
                hp.add_data(fname1, ['three', 7, 8, 9])
                
                hp.add_data(fname2, ['one', 1, 2, 3])
                hp.add_data(fname2, ['two', 4, 5, 6])
                hp.add_data(fname2, ['three', 7, 8, 9])
                
                rows1 = hp.read_data_log(fname1)
                rows2 = hp.read_data_log(fname2)
                info("Wrote 3 rows. Reading back test 1:")
                for r in rows1: print(r)
                info("Wrote 3 rows. Reading back test 2:")
                for r in rows2: print(r)
            
                info("Test 6 completed.")

            elif test == 7:
                # RTC set/get
                info("Test 7: Setting RTC (keep date, set minute to 30, seconds to 0), then read.")
                # Partial set: only update some fields (HydraPurr handles keeping others)  :contentReference[oaicite:3]{index=3}
                hp.set_time(mn=30, sc=0)
                info(" Current time (string):", hp.get_time(as_string=True))
                info(" Current time (dict):", hp.get_time(as_string=False))
                info("Test 7 completed.")

            elif test == 8:
                # RFID read (limited attempts)
                info("Test 8: RFID read (5 attempts).")
                for i in range(5):
                    data = hp.read_rfid()
                    if data is None:
                        print(" No valid package.")
                    else:
                        print(" Interpreted:", data)
                    time.sleep(2)
                info("Test 8 completed.")

            else:
                info(f"Unknown test id: {test}")

        except Exception as e:
            # Keep the loop going even if a device is missing
            info(f"[ERROR] Test {test} raised: {e}")

        time.sleep(2)
        info(f"=== Finished Test {test} ===")

if __name__ == "__main__":
    main()
    tail_to_console()
