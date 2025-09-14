import time
from components.MyStore import MyStore


class LickCounter:
    def __init__(self, cat_name=None, clear_log=False, file_name="licks.csv"):
        # thresholds and state
        self.min_lick_ms = 50
        self.max_lick_ms = 150
        self.min_licks_per_bout = 3
        self.max_bout_gap_ms = 1000
        self.debounce_ms = 5
        self.lick_count = 0
        self.bout_count = 0
        self.state = 0
        self.candidate_state = 0
        self.candidate_since = None
        self.state_since = time.monotonic() * 1000.0
        self.last_lick_end_ms = None
        self.cat_name = str(cat_name)
        # logging: ISO timestamps with milliseconds, header auto if file is new/empty
        header = ["cat_name", "state","licks","bouts"]
        self.store = MyStore(file_name, fmt='iso', with_ms=True, auto_header=header, time_label="time")
        if clear_log:
            self.store.empty()
            self.store.header(header, label="time")
        self.last_logged = (None, None, None, None)
    
    def read_data_log(self):
        lines = self.store.read()
        return lines
    
    def accept_state(self, s, t_ms):
        # accept state transition, update lick/bout counters
        prev, dur_ms = self.state, (t_ms - self.state_since)
        if prev == 1 and s == 0 and self.min_lick_ms <= dur_ms <= self.max_lick_ms: self.lick_count += 1; self.last_lick_end_ms = t_ms
        elif prev == 1 and s == 0: self.last_lick_end_ms = t_ms
        if self.last_lick_end_ms is not None and prev == 0 and self.lick_count >= self.min_licks_per_bout and (t_ms - self.last_lick_end_ms) >= self.max_bout_gap_ms: self.bout_count += 1; self.lick_count = 0; self.last_lick_end_ms = None
        self.state = s; self.state_since = t_ms

    def process_sample(self, sample, t_ms=None):
        # process one binary sample (0/1) and log on meaningful change
        if t_ms is None: t_ms = time.monotonic() * 1000.0
        s = 1 if sample == 1 else 0
        if self.debounce_ms > 0:
            if s != self.candidate_state: self.candidate_state = s; self.candidate_since = t_ms; return
            if self.candidate_since is not None:
                if (t_ms - self.candidate_since) < self.debounce_ms: return
                if s != self.state: self.accept_state(s, t_ms)
                self.candidate_since = None
        else:
            if s != self.state: self.accept_state(s, t_ms)
        if self.state == 0 and self.last_lick_end_ms is not None and self.lick_count >= self.min_licks_per_bout and (t_ms - self.last_lick_end_ms) >= self.max_bout_gap_ms: self.bout_count += 1; self.lick_count = 0; self.last_lick_end_ms = None

        current = (s, self.lick_count, self.bout_count)
        if current != self.last_logged:
            self.store.add([self.cat_name, s, self.lick_count, self.bout_count])   # timestamp auto-prepended by MyStore
            self.last_logged = current

    def get_bout_count(self): 
        # return current bout count
        return self.bout_count

    def reset_counters(self):
        # reset lick and bout counters
        self.lick_count = 0; self.bout_count = 0; self.last_lick_end_ms = None
        
    def get_state(self, beautify=False):
        part0 = str(self.cat_name)
        part1 = str(self.lick_count)
        part2 = str(self.bout_count)
        if not beautify:
            state = part0 + '_' + part1 + '_' + part2
            return state
        else:
            state = f'{part0}" licks {part1}, bouts {part2}'
            return state
        
        

