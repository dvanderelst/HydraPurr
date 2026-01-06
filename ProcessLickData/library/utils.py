import pandas as pd

# This code filters double 0s (and 1s) in the lick state
# This is needed as lick/bout changes are also in the record
# These also have state = 0, but come after the lick event is over.

def filter_lick_events(contents):
    licks = contents.licks
    line_count = licks.shape[0]
    retained_lines = []
    previous_state = 0
    for line_nr in range(0, line_count):
        current_line = licks.iloc[line_nr, :]
        current_state = int(current_line['state'])
        if previous_state == 0 and current_state == 1:
            retained_lines.append(current_line)
        if previous_state == 1 and current_state == 0:
            retained_lines.append(current_line)
        previous_state = current_state * 1

    retained_lines = pd.DataFrame(retained_lines)
    print('Lick events filtered:')
    print('Original Lines:', line_count)
    print('Retained Lines:', retained_lines.shape[0])
    print("-" * 55)
    return retained_lines

def check_time_increases(df):
    value = df['time'] > df['time'].shift(1)
    df.insert(loc=1, column='time_increases', value = value)
    return df
