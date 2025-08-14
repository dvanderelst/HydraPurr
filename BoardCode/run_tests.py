import myADC
import myPixel
import myDigital
import myBT
import myOLED
import myRTC
import myRFID

import time
import board
import myStore

# 0 -> blinking indicator LED
# 1 -> switching relay
# 2 -> Screen test
# 3 -> Water level reading
# 4 -> Testing bluetooth module
# 5 -> Lick detection
# 6 -> Reading writing SD
# 7 -> Setting RTC time
# 8 -> Test RFID module

tests = [0,1,2,3,4,5,7]

for test in tests:

    print(f"Starting Test {test}...")
    time.sleep(2)  # Pause before starting the test for better clarity

    # This test blinks the indicator LED
    if test == 0:
        print("Test 0: Blinking the indicator LED.")
        indicator_led = myDigital.MyDigital(board.D25, 'output')
        for x in range(20):
            print(f"Blink {x + 1}")
            indicator_led.write(True)
            time.sleep(0.1)
            indicator_led.write(False)
            time.sleep(0.1)
        print("Test 0 completed.\n")

    # This test switches on and off the relay
    if test == 1:
        print("Test 1: Switching on and off the relay.")
        relay = myDigital.MyDigital(board.D6, 'output')
        for x in range(3):
            print(f"Relay cycle {x + 1}")
            relay.write(True)
            time.sleep(3)
            relay.write(False)
            time.sleep(3)
        print("Test 1 completed.\n")

    # This tests the screen
    if test == 2:
        print("Test 2: Testing the screen.")
        oled = myOLED.MyOLED()
        for x in range(10):
            print(f"Displaying {x} on the screen.")
            oled.write(x, 5, 0, scale=2)
            time.sleep(1)
        print("Test 2 completed.\n")

    # This tests the water level reading
    if test == 3:
        print("Test 3: Testing the water level reading.")
        water_level = myADC.MyADC(0)
        for x in range(10):
            value = water_level.mean()
            print(f"Reading {x}: {value}")
            time.sleep(1)
        print("Test 3 completed.\n")

    # This tests the Bluetooth module
    if test == 4:
        print("Test 4: Testing the Bluetooth module.")
        bt = myBT.MyBT()
        for x in range(10):
            msg = f"Sending {x}\n"
            print(f"Sending message: {msg.strip()}")
            bt.send(msg)
            time.sleep(0.25)
        print("Test 4 completed.\n")

    # This tests the detection of the lick
    if test == 5:
        print("Test 5: Testing lick detection.")
        lick = myADC.MyADC(1)
        for x in range(50):
            lick_value = lick.read()
            print(f"Lick {x + 1}: {lick_value}")
            time.sleep(0.5)
        print("Test 5 completed.\n")

    # This tests writing to the SD card
    if test == 6:
        print("Test 6: Testing writing to the SD card.")
        mystore = myStore.MyStore()
        mystore.erase()
        mystore.add(['one', 1, 2, 3])
        mystore.add(['two', 1, 2, 3])
        mystore.add(['three', 1, 2, 3])
        print("Done writing to SD card.")
        print("Test 6 completed.\n")

    # This tests setting the time in the RTC
    if test == 7:
        print("Test 7: Setting the time in the RTC.")
        structure = {
            'year': 2024,
            'month': 12,
            'date': 9,
            'hours': 10,
            'minutes': 30,
            'seconds': 0,
            'weekday': 1
        }
        myRTC.set_time(structure)
        print(f"RTC set to: {structure}")
        print("Test 7 completed.\n")

    # This tests the RFID module
    if test == 8:
        print("Test 8: Testing the RFID module.")
        rfid_reader = myRFID.MyRFID()
        for _ in range(5):  # Limiting iterations for testing
            data_package = rfid_reader.read_data_package()
            if data_package:
                print(f"Received Data Package: {data_package}")
                interpreted_data = rfid_reader.interpret_data_package(data_package)
                print(f"Interpreted Data: {interpreted_data}")
            else:
                print("Failed to receive a valid data package.")
            time.sleep(2)  # Pause between attempts
        print("Test 8 completed.\n")

    time.sleep(3)  # Pause between tests
    print(f"Finished Test {test}. Waiting for the next test...\n")
