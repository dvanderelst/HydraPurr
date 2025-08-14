import pandas
import numpy
from LickLibrary import myTimeSeriesPlot
from matplotlib import pyplot
from scipy.interpolate import interp1d
from LickLibrary import LickCounter
from matplotlib import pyplot as plt

file_name = 'recordings/Wed_Mar_13_08_52_55_2024.txt'

data = pandas.read_csv(file_name,skiprows=0, header=None)
values = data.iloc[:, 2]
values = numpy.array(values)

licks = data.iloc[:, 3]
licks = numpy.array(licks)

bouts = data.iloc[:, 4]
bouts = numpy.array(bouts)

timing = data.iloc[:, 0]
timing = pandas.to_datetime(timing)
first_time = timing[0]

#timing = timing - first_time
#timing = timing.dt.total_seconds()

differences = numpy.diff(timing)

buttons = data.iloc[:, 5]

# Plot data on each subplot
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True)
ax1.plot(timing, values, '.-')
ax1.grid()

ax2.plot(timing, licks, '.-')
ax2.grid()

ax3.plot(timing, bouts, '.-')
ax3.set_xlabel('x')
ax3.grid()

# ax4.plot(timing, buttons, '.-')
# ax4.set_xlabel('x')
# ax4.grid()


# Adjust layout to prevent overlap
plt.tight_layout()

# Show the plot
plt.show()

plt.figure()
plt.plot(differences)
plt.show()


