# Run this script to set the time and date on the logger

from HydraPurr import HydraPurr
hp = HydraPurr()

# To skip setting fields, set the field to None
yr=2025
mt=9
dy=20
hr=10
mn=0
sc=0

hp.set_time(yr=yr, mt=mt, dy=dy, hr=hr, mn=0, sc=0)
line1 = " Current time (string):" + str(hp.get_time(as_string=True))
line2 = " Current time (dict):" + str(hp.get_time(as_string=False))
print(line1)
print(line2)