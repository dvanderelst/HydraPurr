import time
from components.MyStore import MyStore


def now(): return time.monotonic() * 1000.0


class LickState:
    def __init__(self, cat_name):
        self.cat_name = cat_name
        self.lick_count = 0
        self.bout_count = 0
        self.state = 0  # debounced (accepted) state
        self.state_since = now()
        self.candidate_state = 0  # raw candidate state
        self.candidate_since = None
        self.last_lick_end_ms = None

        # Parameters
        self.debounce_ms = 5
        self.min_lick_ms = 50
        self.max_lick_ms = 150
        self.min_licks_per_bout = 3
        self.max_bout_gap_ms = 1000

    def process_sample(self, sample):
        """
        Feed one raw sample (0/1).
        Returns: (prev, curr, duration_ms, lick_added, bout_closed)
        """
        current_time = now()
        previous, current, duration = self.debounce_state(sample)

        lick_added = False
        bout_closed = False

        # On any debounced falling edge (1 -> 0): mark end time and (maybe) count lick
        if previous == 1 and current == 0:
            self.last_lick_end_ms = current_time
            if self.min_lick_ms <= duration <= self.max_lick_ms:
                self.lick_count += 1
                lick_added = True

        # Bout closing logic: only when we're in 0 and we've seen at least one valid lick
        if current == 0 and self.lick_count > 0:
            gap = current_time - self.last_lick_end_ms
            if gap >= self.max_bout_gap_ms:
                if self.lick_count >= self.min_licks_per_bout:
                    self.bout_count += 1
                    bout_closed = True
                # Reset per-bout lick counter regardless (bout ended or fizzled)
                self.lick_count = 0

        return previous, current, duration, lick_added, bout_closed

    def debounce_state(self, sample):
        t = now()
        previous_state = self.state
        duration = t - self.state_since  # how long current state has been held

        # 1) New candidate
        if sample != self.candidate_state:
            self.candidate_state = sample
            self.candidate_since = t
            return previous_state, self.state, duration  # no change yet

        # 2) Candidate == stable state
        if self.candidate_state == self.state:
            return previous_state, self.state, duration

        # 3) Candidate differs, check debounce
        if t - self.candidate_since >= self.debounce_ms:
            self.state = self.candidate_state
            self.state_since = t
            return previous_state, self.state, duration  # duration is how long prev. state lasted

        # 4) Not stable long enough
        return previous_state, self.state, duration

    def end_bout(self, hard=True, finalize_current_lick=True):
        current_time = now()
        lick_finalized = False
        lick_duration = None
        bout_closed = False

        # Optionally finalize the ongoing lick at 'current_time'
        if finalize_current_lick and self.state == 1:
            lick_duration = current_time - self.state_since
            self.last_lick_end_ms = current_time
            if self.min_lick_ms <= lick_duration <= self.max_lick_ms:
                self.lick_count += 1
                lick_finalized = True

        # Close bout immediately if there were valid licks
        if self.lick_count > 0:
            if self.lick_count >= self.min_licks_per_bout:
                self.bout_count += 1
                bout_closed = True
            # Reset per-bout counter regardless (bout ended or fizzled)
            self.lick_count = 0

        if hard:
            # Reset debouncer to idle; start fresh when this cat is active again
            self.state = 0
            self.candidate_state = 0
            self.state_since = current_time
            self.candidate_since = None
            # Ensure last_lick_end_ms is defined after forcing idle
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
        current_active_cat = self.active_cat_name
        state = self.states[current_active_cat]
        state.end_bout()
        self.log_data(current_active_cat)
        self.active_cat_name = cat_name

    def get_active_state(self):
        return self.states.get(self.active_cat_name)

    def clear_log(self):
        self.store.empty()
        self.store.header(self.header, label="time")

    def read_data_log(self):
        lines = self.store.read()
        return lines

    def update(self, sample, cat_name=None):
        if cat_name is None: cat_name = self.active_cat_name
        state = self.states.get(cat_name)
        previous_state_string = self.get_state_string(cat_name=cat_name)
        prev, curr, dur, lick_added, bout_closed = state.process_sample(sample)
        current_state_string = self.get_state_string(cat_name=cat_name)
        if previous_state_string != current_state_string: self.log_data(cat_name=cat_name)
        result = {}
        result['cat_name'] = state.cat_name
        result['previous_state'] = prev
        result['current_state'] = curr
        result['state_duration_ms'] = dur
        result['lick_added'] = lick_added
        result['bout_closed'] = bout_closed
        result['lick_count'] = state.lick_count
        result['bout_count'] = state.bout_count
        result['state_string'] = current_state_string
        return result

    def get_bout_count(self, cat_name=None):
        # return current bout count for specified cat (or active cat if None)
        if cat_name is None: cat_name = self.active_cat_name
        state = self.states.get(cat_name)
        return state.bout_count

    def get_lick_count(self, cat_name=None):
        # return current lick count for specified cat (or active cat if None)
        if cat_name is None: cat_name = self.active_cat_name
        state = self.states.get(cat_name)
        return state.lick_count

    def get_state_string(self, cat_name=None):
        if cat_name is None: cat_name = self.active_cat_name
        state = self.states.get(cat_name)
        return f"{cat_name}: state={state.state} licks={state.lick_count} bouts={state.bout_count}"

    def get_state_data(self, cat_name=None):
        if cat_name is None: cat_name = self.active_cat_name
        state = self.states.get(cat_name)
        data = [cat_name, state.state, state.lick_count, state.bout_count]
        return data

    def log_data(self, cat_name=None):
        if cat_name is None: cat_name = self.active_cat_name
        data = self.get_state_data(cat_name=cat_name)
        self.store.add(data)
