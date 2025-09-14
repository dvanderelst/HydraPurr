import time
from components.MyStore import MyStore

def now(): return int(time.monotonic() * 1000)  # int ms for consistency

class LickState:
    def __init__(self, cat_name):
        self.cat_name = cat_name
        self.lick_count = 0
        self.bout_count = 0
        self.state = 0
        self.state_since = now()
        self.candidate_state = 0
        self.candidate_since = None
        self.last_lick_end_ms = None
        # Parameters
        self.debounce_ms = 5
        self.min_lick_ms = 50
        self.max_lick_ms = 150
        self.min_licks_per_bout = 3
        self.max_bout_gap_ms = 1000

    def process_sample(self, sample):
        current_time = now()
        previous, current, duration = self.debounce_state(sample)
        lick_added, bout_closed = False, False

        # Falling edge (1->0): finalize lick
        if previous == 1 and current == 0:
            self.last_lick_end_ms = current_time
            if self.min_lick_ms <= duration <= self.max_lick_ms:
                self.lick_count += 1
                lick_added = True

        # Close bout if quiet long enough and we had licks
        if current == 0 and self.lick_count > 0:
            gap = current_time - self.last_lick_end_ms
            if gap >= self.max_bout_gap_ms:
                if self.lick_count >= self.min_licks_per_bout:
                    self.bout_count += 1
                    bout_closed = True
                self.lick_count = 0  # reset per-bout counter

        return previous, current, duration, lick_added, bout_closed

    def debounce_state(self, sample):
        t = now()
        previous_state = self.state
        duration = t - self.state_since

        if sample != self.candidate_state:
            self.candidate_state = sample
            self.candidate_since = t
            return previous_state, self.state, duration

        if self.candidate_state == self.state:
            return previous_state, self.state, duration

        if self.candidate_since is not None and (t - self.candidate_since) >= self.debounce_ms:
            self.state = self.candidate_state
            self.state_since = t
            return previous_state, self.state, duration

        return previous_state, self.state, duration

    def end_bout(self, hard=True, finalize_current_lick=True):
        current_time = now()
        lick_finalized, lick_duration, bout_closed = False, None, False

        if finalize_current_lick and self.state == 1:
            lick_duration = current_time - self.state_since
            self.last_lick_end_ms = current_time
            if self.min_lick_ms <= lick_duration <= self.max_lick_ms:
                self.lick_count += 1
                lick_finalized = True

        if self.lick_count > 0:
            if self.lick_count >= self.min_licks_per_bout:
                self.bout_count += 1
                bout_closed = True
            self.lick_count = 0

        if hard:
            self.state = 0
            self.candidate_state = 0
            self.state_since = current_time
            self.candidate_since = None
            if self.last_lick_end_ms is None:
                self.last_lick_end_ms = current_time

        return lick_finalized, lick_duration, bout_closed

class LickCounter:
    def __init__(self, cat_names=None, clear_log=False, file_name="licks.csv"):
        if cat_names is None: cat_names = ['unknown']
        if 'unknown' not in cat_names: cat_names.insert(0, 'unknown')
        self.active_cat_name = 'unknown'
        self.cat_names = cat_names
        self.header = ["cat_name", "state", "licks", "bouts"]
        self.store = MyStore(file_name, fmt='iso', with_ms=True, auto_header=self.header, time_label="time")
        if clear_log: self.clear_log()
        self.states = {name: LickState(name) for name in cat_names}

    def set_active_cat(self, cat_name):
        if cat_name == self.active_cat_name: return
        prev_cat = self.active_cat_name
        self.states[prev_cat].end_bout()   # finalize previous cat
        self.log_data(prev_cat)            # log closure/reset for prev cat
        self.active_cat_name = cat_name
        # Optional: also log an entry for the new active cat immediately:
        # self.log_data(cat_name)

    def get_active_state(self): return self.states.get(self.active_cat_name)

    def clear_log(self):
        self.store.empty()
        self.store.header(self.header, label="time")

    def read_data_log(self): return self.store.read()

    def update(self, sample, cat_name=None):
        if cat_name is None: cat_name = self.active_cat_name
        state = self.states.get(cat_name)
        previous_state_string = self.get_state_string(cat_name=cat_name)
        prev, curr, dur, lick_added, bout_closed = state.process_sample(sample)
        current_state_string = self.get_state_string(cat_name=cat_name)
        if previous_state_string != current_state_string: self.log_data(cat_name=cat_name)
        return {
            "cat_name": state.cat_name,
            "previous_state": prev,
            "current_state": curr,
            "state_duration_ms": dur,
            "lick_added": lick_added,
            "bout_closed": bout_closed,
            "lick_count": state.lick_count,
            "bout_count": state.bout_count,
            "state_string": current_state_string,
        }

    def get_bout_count(self, cat_name=None):
        if cat_name is None: cat_name = self.active_cat_name
        return self.states.get(cat_name).bout_count

    def get_lick_count(self, cat_name=None):
        if cat_name is None: cat_name = self.active_cat_name
        return self.states.get(cat_name).lick_count

    def get_state_string(self, cat_name=None):
        if cat_name is None: cat_name = self.active_cat_name
        s = self.states.get(cat_name)
        return f"{cat_name}: state={s.state} licks={s.lick_count} bouts={s.bout_count}"

    def get_state_data(self, cat_name=None):
        if cat_name is None: cat_name = self.active_cat_name
        s = self.states.get(cat_name)
        return [cat_name, s.state, s.lick_count, s.bout_count]

    def log_data(self, cat_name=None):
        if cat_name is None: cat_name = self.active_cat_name
        self.store.add(self.get_state_data(cat_name=cat_name))
