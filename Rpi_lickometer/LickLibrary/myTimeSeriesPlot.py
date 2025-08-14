import matplotlib.pyplot as plt
import numpy as np

class myTimeSeriesPlot:
    def __init__(self, data, sample_rate):
        self.data = data
        self.sample_rate = sample_rate
        self.fig, self.ax = plt.subplots()
        self.ax.plot(np.arange(len(data)) / sample_rate, data, marker='o', linestyle='-')
        self.fig.canvas.mpl_connect('close_event', self.on_close)

    def measure_time_difference(self):
        while True:
            points = plt.ginput(n=2, timeout=0)
            if len(points) != 2:
                break
            x1, y1 = points[0]
            x2, y2 = points[1]
            idx1 = int(x1 * self.sample_rate)
            idx2 = int(x2 * self.sample_rate)
            time_difference = abs(idx2 - idx1) / self.sample_rate
            self.fig.suptitle(f"Time difference: {time_difference} seconds")
            plt.draw()

    def on_close(self, event):
        plt.close(self.fig)

# # Example time series data
# data = np.random.randint(0, 100, size=100)
# sample_rate = 1  # Assuming data is sampled at 1 Hz
#
# # Create TimeSeriesPlot instance
# ts_plot = TimeSeriesPlot(data, sample_rate)
#
# plt.title('Time Series Data')
# plt.xlabel('Time (seconds)')
# plt.ylabel('Value')
# plt.grid(True)
#
# ts_plot.measure_time_difference()
#
# plt.show()
