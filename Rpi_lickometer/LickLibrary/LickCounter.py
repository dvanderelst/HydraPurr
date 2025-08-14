def integers_with_names(names, integers):
    output = ' '.join(f"{name}: {number}" for name, number in zip(names, integers))
    return output


class LickCounter:
    def __init__(self, min_lick_length, max_lick_length, min_licks_per_bout, max_bout_gap):
        self.min_lick_length = min_lick_length
        self.max_lick_length = max_lick_length
        self.max_bout_gap = max_bout_gap
        self.min_licks_per_bout = min_licks_per_bout
        self.lick_count = 0
        self.bout_count = 0

        self.ones_count = 0
        self.zeros_count = 0

    def correct_lick_length(self):
        return self.min_lick_length <= self.ones_count <= self.max_lick_length

    def process_sample(self, sample):
        if sample == 1:
            self.ones_count += 1
            self.zeros_count = 0

        if sample == 0:
            self.zeros_count += 1

            if self.lick_count >= self.min_licks_per_bout:
                if self.zeros_count >= self.max_bout_gap:
                    self.bout_count += 1
                    self.lick_count = 0

            if self.zeros_count > self.max_bout_gap:
                self.lick_count = 0

            if self.correct_lick_length():
                self.lick_count += 1

            self.ones_count = 0

    def get_bout_count(self):
        return self.bout_count

    def reset_counters(self):
        self.bout_count = 0
        self.lick_count = 0
        self.ones_count = 0

    def print_status(self):
        names = ['ones', 'licks', 'bouts']
        values = [self.ones_count, self.lick_count, self.bout_count]
        text = integers_with_names(names, values)
        print(text, end='\r')


if __name__ == "__main__":
    import time
    from LickLibrary import myKeyboard
    bouts_to_deployment = 3
    counter = LickCounter(5, 10, 3, 10)
    while True:
        sample = int(myKeyboard.is_key_pressed('/dev/input/event4'))
        counter.process_sample(sample)
        counter.print_status()
        bout_count = counter.get_bout_count()
        if bout_count >= bouts_to_deployment:
            print()
            print('deploying')
            time.sleep(1)
            counter.reset_counters()
        time.sleep(0.1)

