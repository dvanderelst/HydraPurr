import plotly.graph_objects as go

from library import compute_lick_durations_ms, data_reader


data_reader.print_data_folders_table()
contents = data_reader.read_data_folder(0)
licks = contents.licks
licks['dummy'] = 1
on_states = licks.query('state == 1')


scatter_line = go.Scatter(x=on_states.time, y=licks.dummy, mode="lines+markers")

fig = go.Figure()
fig.add_trace(scatter_line)
fig.show(renderer='browser')
