import time
import collections
from LickLibrary import Control
import threading
from LickLibrary import myKeypad

def time2name():
    txt = time.asctime()
    while '  ' in txt: txt = txt.replace('  ', ' ')
    txt = txt.replace(' ', '_')
    txt = txt.replace(':', '_')
    return txt


class Recorder:
    def __init__(self, rate, verbose=False):
        self.rate = rate
        self.verbose = verbose
        self.counter = 1
        self.buffer_length = 10 * self.rate
        self.use_analog = True
        self.detector = Control.LickDetector(analog=self.use_analog)
        self.keypad = myKeypad.myKeypad()
        self.buffer = collections.deque(maxlen=self.buffer_length)
        self.buffer_time = collections.deque(maxlen=self.buffer_length)
        self.buffer_keys = collections.deque(maxlen=self.buffer_length)

        self.recording = collections.deque()
        self.recording_keys = collections.deque()
        self.recording_time = collections.deque()

        self.use_buffer = True
        self.stop_record = False
        self.thread = None
        self.start_time = 0

    def stop(self):
        self.stop_record = True

    def start(self):
        self.stop_record = False
        self.thread = threading.Thread(target=self.record_loop, daemon=True)
        self.thread.start()

    def record_loop(self):
        self.start_time = time.time()
        while not self.stop_record:
            self.add_sample()
            time.sleep(1 / self.rate)
            self.counter += 1

    def status(self, to_screen=False):
        txt1 = 'Buffer length: ' + str(len(self.buffer))
        txt2 = 'Recording length: ' + str(len(self.recording))
        txt = txt1 + '\n' + txt2
        if to_screen: print(txt)
        return txt

    def add_sample(self):
        value = self.detector.get_lick()
        key = self.keypad.get_key()
        stamp = time.time() - self.start_time

        if self.verbose and self.counter % self.rate == 0:
            print('Recording', value, key, stamp)
            self.counter = 1

        if self.use_buffer:
            self.buffer.append(value)
            self.buffer_keys.append(str(key))
            self.buffer_time.append(stamp)
        else:
            self.recording.append(value)
            self.buffer_keys.append(str(key))
            self.recording_time.append(stamp)

    def get_all(self):
        buffer = list(self.buffer)
        recording = list(self.recording)
        total = buffer + recording

        buffer_keys = list(self.buffer_keys)
        recording_keys = list(self.recording_keys)
        total_keys = buffer_keys + recording_keys

        buffer_time = list(self.buffer_time)
        recording_time = list(self.recording_time)
        total_time = buffer_time + recording_time
        return total, total_keys, total_time

    def get_data(self):
        result = ''
        total, total_keys, total_time = self.get_all()
        for t, v, k in zip(total_time, total, total_keys):
            line = str(t) + ',' + str(v) + ',' + str(k) + '\n'
            result = result + line
        result = result.rstrip('\n')
        return result

    def plot(self):
        from matplotlib import pyplot #to allow running on a system without matplotlib
        print('Plotting...')
        total, _, total_time = self.get_all()
        pyplot.figure()
        pyplot.plot(total_time, total)
        pyplot.show()
