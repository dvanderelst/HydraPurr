from LickLibrary import hx711
from LickLibrary import Settings
import time


# Place nothing on the scale, run the calibration.py and record the output. That is the offset.
# Place a known weight like 1kg(1000g) on the scale, record the output as w.
# Calculate the ratio
# ratio = (w - offset) / known weight

def name2nr(scale_name):
    if scale_name == 'lick': return 1
    if scale_name == 'feeder': return 2


class myScale:
    def __init__(self, scale_id=1):
        if type(scale_id) == str: scale_id = name2nr(scale_id)
        self.scale_id = scale_id
        if scale_id == 1: self.scale = hx711.HX711(dout=Settings.dout_pin1, pd_sck=Settings.pd_sck_pin1)
        if scale_id == 2: self.scale = hx711.HX711(dout=Settings.dout_pin2, pd_sck=Settings.pd_sck_pin2)

    def calibrate(self, calibration_weight=355):
        self.scale.set_offset(0)
        self.scale.set_scale(1)

        print('Remove weight from scale')
        time.sleep(3)
        offset = self.scale.get_grams()

        print('place calibration weight of', calibration_weight, 'grams')
        time.sleep(3)
        w = self.scale.get_grams()

        ratio = (w - offset) / calibration_weight
        print('---- Results:')
        print('w', w)
        print('ratio', ratio)
        line1 = "offset%s = %.5f" % (self.scale_id, offset)
        line2 = "ratio%s = %.5f" % (self.scale_id, ratio)

        self.scale.set_offset(offset)
        self.scale.set_scale(ratio)
        test_measurement = self.scale.get_grams()

        print('Test Measurement:', test_measurement)
        print('-----')
        print('Add this code to Settings.py:')
        print(line1)
        print(line2)

    def measure(self, repeats=1):
        self.scale.set_offset(Settings.offset1)
        self.scale.set_scale(Settings.ratio1)
        w = self.scale.get_grams(repeats)
        return w
