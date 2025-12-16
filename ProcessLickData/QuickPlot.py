import pandas as pd
import plotly.express as px

data = pd.read_csv('data/licks.dat')
# make time in data a time series
data['time'] = pd.to_datetime(data['time'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
data = data.query('state==1')
# make a quick plot of the data (water as function of time)
# use plotly

fig = px.line(data, x='time', y='water', title='Licks over Time', labels={'time': 'Time', 'water': 'Water Licks'})
fig.update_traces(mode='lines+markers', marker=dict(size=6))

fig.show(renderer='browser')


