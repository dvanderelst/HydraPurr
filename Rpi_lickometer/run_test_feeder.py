import time

from LickLibrary import Control
feeder = Control.Feeder()

for i in range(1000):
    print(i)
    feeder.on()
    time.sleep(5)
    feeder.off()
    time.sleep(3)

