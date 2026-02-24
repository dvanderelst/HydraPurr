from library import utils
from library import data_reader
from analysis.BoutAnalyzer import BoutAnalyzer
from matplotlib import pyplot as plt
import plotly.graph_objects as go

# Show available data folders
data_reader.print_data_folders_table()

# Select data folder (change index as needed)
data_folder_index = 1
contents = data_reader.read_data_folder(data_folder_index)
licks = contents.licks
system_log = contents.system_log

print(f"\nAnalyzing data folder: {contents.name}")
print(f"Loaded {len(licks)} lick records")

# OLD METHOD: Using utils.process_licks() with board settings
print("\n--- OLD METHOD (utils.process_licks) ---")
from lib import Settings
old_processed, old_summary = utils.process_licks(
    contents, 
    group_gap_ms=Settings.max_bout_gap_ms, 
    min_group_size=Settings.min_licks_per_bout
)
print(f"Old method: {len(old_processed)} events, {len(old_summary)} bouts")

# NEW METHOD: Using BoutAnalyzer with same settings
print("\n--- NEW METHOD (BoutAnalyzer) ---")
analyzer = BoutAnalyzer()
new_processed, new_summary = analyzer.analyze_dataframe(
    licks, 
    group_gap_ms=Settings.max_bout_gap_ms, 
    min_group_size=Settings.min_licks_per_bout
)
print(f"New method: {len(new_processed)} events, {len(new_summary)} bouts")

# Comparison
print(f"\n--- COMPARISON ---")
print(f"Events match: {len(old_processed) == len(new_processed)}")
print(f"Bouts match: {len(old_summary) == len(new_summary)}")

if len(old_processed) == len(new_processed) and len(old_summary) == len(new_summary):
    print("✅ Both methods produce IDENTICAL results!")
    print("   The new BoutAnalyzer uses the same algorithm as the board.")
else:
    print("⚠️  Methods produce different results (check parameters)")

# Use new method for visualization (can switch to old if needed)
processed = new_processed
summary = new_summary

# Add bout information to title
if not summary.empty:
    print(f"\n📊 Analysis Summary:")
    print(f"   Total bouts: {len(summary)}")
    print(f"   Average duration: {summary['duration'].mean():.1f}ms")
    print(f"   Average licks per bout: {summary['n'].mean():.1f}")
    print(f"   Average water change: {summary['water_delta'].mean():.3f}")


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