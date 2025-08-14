import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from statsmodels.formula.api import ols

data = pd.read_csv('data/sensor_measures.csv')
data.columns = data.columns.str.strip()

selected = data.query('tester in ["LV"]')
selected = selected.query('voltage < 2500')
selected = selected.query('weight > 50')
selected = selected.query('weight < 400')
run = selected['test_num']

#%%

unique_runs = run.unique()
all_diff_weight = []
all_diff_voltage = []
all_run_array = []
for selected_run in unique_runs:
    run_data = selected.query('test_num == @selected_run')
    weight = run_data['weight']
    voltage = run_data['voltage']
    weight = weight.values
    voltage = voltage.values

    n_samples = len(weight)
    first_points = np.random.choice(range(n_samples), 1000, replace=True)
    second_points = np.random.choice(range(n_samples), 1000, replace=True)

    first_weight = weight[first_points]
    first_voltage = voltage[first_points]
    second_weight = weight[second_points]
    second_voltage = voltage[second_points]

    diff_weight = first_weight - second_weight
    diff_voltage = first_voltage - second_voltage

    lower_voltage = diff_voltage < 0
    diff_weight = diff_weight[lower_voltage]
    diff_voltage = diff_voltage[lower_voltage]


    lower_weight = (diff_weight < 0) * (diff_weight > -100)
    diff_weight = diff_weight[lower_weight]
    diff_voltage = diff_voltage[lower_weight]

    run_array = np.ones_like(diff_weight) * selected_run

    all_diff_weight.extend(diff_weight)
    all_diff_voltage.extend(diff_voltage)
    all_run_array.extend(run_array)

data = pd.DataFrame({'run': all_run_array, 'diff_weight': all_diff_weight, 'diff_voltage': all_diff_voltage})

plt.figure()
plt.scatter(data.diff_voltage, data.diff_weight, c=data.run, cmap='viridis')
plt.ylabel('Weight difference')
plt.xlabel('Voltage difference')
plt.title(f'Run {selected_run}')
plt.show()


#     sampled_indices = np.random.choice(range(n_samples), 1000, replace=True)
#     sampled_weight = weight.iloc[sampled_indices]
#     sampled_voltage = voltage.iloc[sampled_indices]
#     diff_sampled_indices = np.diff(sampled_indices)
#     diff_weight = np.diff(sampled_weight)
#     diff_voltage = np.diff(sampled_voltage)
#
#     print(len(diff_weight))
#     diff_weight = diff_weight[diff_sampled_indices > 0]
#     diff_voltage = diff_voltage[diff_sampled_indices > 0]
#     print(len(diff_weight))
#
#     run_array = np.ones_like(diff_weight) * selected_run
#     all_diff_weight.extend(diff_weight)
#     all_diff_voltage.extend(diff_voltage)
#     all_run_array.extend(run_array)
#
# data = pd.DataFrame({'run': all_run_array, 'diff_weight': all_diff_weight, 'diff_voltage': all_diff_voltage})
#
#
# plt.figure()
# plt.scatter(data.diff_voltage, data.diff_weight, c=data.run, cmap='viridis')
# plt.ylabel('Weight difference')
# plt.xlabel('Voltage difference')
# plt.title(f'Run {selected_run}')
# plt.show()
#
model = ols('diff_weight ~ diff_voltage', data=data)
result = model.fit()
print(result.summary())

# Get the model errors
errors = result.resid
plt.figure()
plt.hist(errors, bins=20)
plt.xlabel('Error')
plt.ylabel('Frequency')
plt.title('Error Distribution')
plt.show()

# plt.figure()
# plt.scatter(run_data.voltage, run_data.weight, c=run_data.test_num)
# plt.xlabel('Voltage')
# plt.ylabel('Weight')
# plt.title('Weight vs Voltage')
# plt.show()