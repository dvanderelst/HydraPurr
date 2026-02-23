from library import utils
from library import data_reader
from matplotlib import pyplot as plt
import plotly.graph_objects as go

data_reader.print_data_folders_table()
contents = data_reader.read_data_folder(1)
licks = contents.licks
system_log = contents.system_log

processed, summary = utils.process_licks(contents, min_group_size=5)


time = processed['time']
water = processed['water']
duration = processed['duration']
water_delta = processed['water_delta']
group = processed['group']
group_index = processed['group_index']

processed["group_str"] = (
    processed["group"].astype("Int64").astype(str).replace("<NA>", "NaN")
)

line_trace = go.Scatter(
    x=processed["time"],
    y=processed["water"],
    mode="lines",
    name="Water Level",
    line={"color": "rgba(0,0,0,0.3)"},
    showlegend=False,
)

# Create scatter plot for lick events
scatter_trace = go.Scatter(
    x=processed["time"],
    y=processed["water"],
    mode="markers",
    name="Lick Events",
    marker={"color": "red", "size": 8},
    showlegend=True,
)

fig = go.Figure(line_trace)
fig.add_trace(scatter_trace)
fig.show(renderer='browser')

# Save the interactive plot as HTML
fig.write_html("lick_analysis_interactive.html")
print("Interactive plot saved as 'lick_analysis_interactive.html'")

#%%
plt.figure()
plt.scatter(summary["duration"], -summary["water_delta"], c = summary["group"], cmap='jet')
plt.colorbar()
plt.show()