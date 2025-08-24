import time
from HydraPurr import HydraPurr
from LickCounter import LickCounter

hp = HydraPurr()
ctr = LickCounter(clear_log=True)

print("Touch the lick sensor to test. Press Ctrl+C to stop.\n")

count = 0
while True:
    s = hp.read_lick(binary=True)
    ctr.process_sample(s)
    print(f"{count} s:{s} licks:{ctr.lick_count} bouts:{ctr.bout_count}       ", end="\r")
    time.sleep(10 / 1000.0)
    count+=1
    if count == 1000: break

log = ctr.read()
for x in log: print(x)
