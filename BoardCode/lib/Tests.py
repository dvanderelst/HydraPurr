import time
import traceback
from HydraPurr import HydraPurr
from TagReader import TagReader
from components.MySystemLog import setup_system_log, set_system_log_level, DEBUG, info
from components.MySystemLog import read_log
from components.MySystemLog import set_time_fn
from components.MyStore import timestamp  # uses your RTC + ms

def test_log(number, message, function=info):
    line = f"[Test {number}] {message}"
    function(line)

def main(selected_tests):
    set_system_log_level(DEBUG)
    set_time_fn(lambda: timestamp('iso', True))  # use RTC time for log timestamps
    setup_system_log()
    info("[Run Tests] Start")
    hp = HydraPurr()

    for test in selected_tests:
        time.sleep(1)
        try:
            if test == 0:
                test_log(0, "Blinking the indicator LED")
                for i in range(10):
                    hp.indicator_on()
                    time.sleep(0.5)
                    hp.indicator_off()
                    time.sleep(0.5)
                test_log(0, "Done")

            elif test == 1:
                test_log(1, "Switching the feeder relay on/off")
                for i in range(3):
                    hp.feeder_on()
                    time.sleep(0.5)
                    hp.feeder_off()
                    time.sleep(0.5)
                test_log(1, "Done")

            elif test == 2:
                test_log(2, "Writing to the screen")
                hp.clear_screen()
                hp.write_line(0, 'Line')
                hp.write_line(1, 'Writing')
                hp.show_screen()
                test_log(2, "Done")

            elif test == 3:
                test_log(3, "Water level reading")
                for i in range(10):
                    hp.read_water_level(samples=50, dt=0.001)
                    time.sleep(1)
                test_log(3, "Done")

            elif test == 4:
                # Bluetooth send
                test_log(4, "Writing bluetooth messages")
                for i in range(10):
                    msg = f"Sending {i}"
                    test_log(4, msg)
                    hp.bluetooth_send(msg)
                    time.sleep(0.25)
                test_log(4, "Done")

            elif test == 5:
                test_log(5, "Lick detection")
                for i in range(50):
                    value = hp.read_lick()
                    test_log(5, f"Lick value: {value}")
                    time.sleep(0.5)
                test_log(5, "Done")

            elif test == 6:
                info(6, "SD logging")
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
                test_log(6, f"Contents of {fname1}:")
                for r in rows1: test_log(6, str(r))
                test_log(6, f"Contents of {fname2}:")
                for r in rows2: test_log(6, str(r))

                test_log(6, "Done")

            elif test == 7:
                # RTC set/get
                test_log(7, "Setting RTC")
                # Partial set: only update some fields (HydraPurr handles keeping others)  :contentReference[oaicite:3]{index=3}
                hp.set_time(mn=30, sc=0)
                logline1 = " Current time (string):" + str(hp.get_time(as_string=True))
                logline2 = " Current time (dict):" + str(hp.get_time(as_string=False))
                test_log(7, logline1)
                test_log(7, logline2)
                test_log(7, "Done")

            elif test == 8:
                start_time = time.time()
                test_log(8, 'RFID reader')
                reader = TagReader()
                reader.reset_now()
                while True:
                    reader.poll()
                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    if elapsed_time > 10: break
                test_log(8, "Done")

        except Exception as e:
            info(f"[ERROR] Test {test} raised: {e}")
            traceback.print_exception(e)
        time.sleep(2)
    log = read_log()
    return hp, log

 