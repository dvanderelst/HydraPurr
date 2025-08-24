# LickCounterTime.py
import time

class LickCounter:
    def __init__(self):
        # Initialize thresholds and counters
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

    def now_ms(self): 
        # Return current time in ms
        return time.monotonic() * 1000.0

    def accept_state(self, s, t_ms):
        # Accept a state transition and update lick/bout counters
        prev, dur_ms = self.state, (t_ms - self.state_since)
        if prev == 1 and s == 0 and self.min_lick_ms <= dur_ms <= self.max_lick_ms: self.lick_count += 1; self.last_lick_end_ms = t_ms
        elif prev == 1 and s == 0: self.last_lick_end_ms = t_ms
        if self.last_lick_end_ms is not None and prev == 0 and self.lick_count >= self.min_licks_per_bout and (t_ms - self.last_lick_end_ms) >= self.max_bout_gap_ms:
            self.bout_count += 1; self.lick_count = 0; self.last_lick_end_ms = None
        self.state = s; self.state_since = t_ms

    def process_sample(self, sample, t_ms=None):
        # Process one binary sample (0/1) at time t_ms
        if t_ms is None: t_ms = self.now_ms()
        s = 1 if sample == 1 else 0
        if self.debounce_ms > 0:
            if s != self.candidate_state: self.candidate_state = s; self.candidate_since = t_ms; return
            if self.candidate_since is not None:
                if (t_ms - self.candidate_since) < self.debounce_ms: return
                if s != self.state: self.accept_state(s, t_ms)
                self.candidate_since = None
        else:
            if s != self.state: self.accept_state(s, t_ms)
        if self.state == 0 and self.last_lick_end_ms is not None and self.lick_count >= self.min_licks_per_bout and (t_ms - self.last_lick_end_ms) >= self.max_bout_gap_ms:
            self.bout_count += 1; self.lick_count = 0; self.last_lick_end_ms = None

    def get_bout_count(self):
        # Return current bout count
        return self.bout_count

    def reset_counters(self):
        # Reset lick and bout counters
        self.lick_count = 0; self.bout_count = 0; self.last_lick_end_ms = None

