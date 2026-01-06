from library import utils
from library import data_reader

data_reader.print_data_folders_table()
contents = data_reader.read_data_folder(0)


licks = utils.check_time_increases(contents.licks)
licks = licks.sort_values('time')
#
#
# lick_events = utils.filter_lick_events(contents)
# line_count = lick_events.shape[0]
# lick_events['time_increases'] = lick_events['time'] > lick_events['time'].shift(1)
# previous_state = 0
# onset_time = None
# for line_nr in range(0, line_count):
#     current_line = lick_events.iloc[line_nr, :]
#     current_state = int(current_line['state'])
#     if previous_state == 0 and current_state == 1:
#         print('Lick started')
#         onset_time = current_line['time']
#     if previous_state == 1 and current_state == 0:
#         offset_time = current_line['time']
#         duration = offset_time - onset_time
#         duration = duration.total_seconds() * 1000
#         print(line_nr, 'Lick ended', duration)
#     previous_state = current_state
#
#
# test = lick_events[['time', 'time_increases']]
#
#
