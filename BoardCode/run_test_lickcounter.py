import time
from HydraPurr import HydraPurr
from LickCounter import LickCounter

hp = HydraPurr()
ctr = LickCounter()
print("Touch the lick sensor to test. Press Ctrl+C to stop.\n")
while True:
    s = hp.read_lick(binary=True)
    ctr.process_sample(s)
    print(f"s:{s} licks:{ctr.lick_count} bouts:{ctr.bout_count}   ", end="\r")
    time.sleep(SAMPLE_MS / 1000.0)

