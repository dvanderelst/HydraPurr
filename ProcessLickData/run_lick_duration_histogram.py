import plotly.graph_objects as go

from library import compute_lick_durations_ms, data_reader


data_reader.print_data_folders_table()
contents = data_reader.read_data_folder(0)
licks = contents.licks
if licks is None:
    raise ValueError("No licks.dat found for the selected folder.")

MAX_DURATION_MS = 2500
durations_ms = compute_lick_durations_ms(licks, max_duration_ms=MAX_DURATION_MS)
if not durations_ms:
    raise ValueError("No lick durations found to plot.")

fig = go.Figure()
fig.add_trace(go.Histogram(x=durations_ms, nbinsx=1000))
fig.update_layout(
    title=f"Lick Duration Histogram - {contents.name}",
    xaxis_title="Lick Duration (ms)",
    yaxis_title="Count",
)
fig.show()
