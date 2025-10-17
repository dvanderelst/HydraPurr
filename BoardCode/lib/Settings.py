
system_log_filename = "system.log"
lick_data_filename = "licks.dat"

clear_system_log_on_start = False
clear_lick_data_on_start = False

cat_timeout_ms = 1000  # switch to 'unknown' if no valid tag is seen for x ms
max_tag_read_hz = 3.0  # change here to adjust read refresh limit (Hz)
deployment_bout_count = 5
deployment_duration_ms = 2000
min_lick_ms = 50
max_lick_ms = 150
min_licks_per_bout = 3
max_bout_gap_ms = 1000

cats={}
cats['61000000007E30010000000000'] = {'name': 'henk', 'age': 6}
cats['32E09C0000ED30010000000000'] = {'name': 'bob', 'age': 12}




