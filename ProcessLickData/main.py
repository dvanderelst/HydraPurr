import pandas
import library
from matplotlib import pyplot
threshold = 10000
#filename = 'data/Mon_Nov_13_17_29_57_2023'
#filename = 'data/Mon_Nov_13_17_46_49_2023'
#filename = 'data/Mon_Nov_13_17_55_13_2023'
#filename = 'data/Mon_Nov_13_17_33_16_2023'
filename = 'data/Mon_Nov_13_17_33_16_2023'

summary = library.summarize(filename)
data, comment = library.read(filename)
summary = summary[1:-1]
lick_durations = summary[summary > 0] / 100
inter_durations = summary[summary < 0] / 100

#lick_durations = lick_durations[lick_durations < 0.5]

pyplot.figure()
pyplot.plot(data.time, data.response)
pyplot.title(comment)
pyplot.show()

pyplot.figure()
pyplot.hist(lick_durations, bins=15)
pyplot.show()