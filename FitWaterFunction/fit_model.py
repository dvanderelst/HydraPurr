import pandas as pd
from library import models
from matplotlib import pyplot as plt

data = pd.read_csv('data/sensor_measures.csv')
data.columns = data.columns.str.strip()
print(data.columns)
selected = data.query('tester in ["LV"]')
selected = selected.query('voltage < 2500')
selected = selected.query('weight > 50')
selected = selected.query('weight < 400')
#selected = selected.query('test_num in [1]')

weight = selected['weight']
voltage = selected['voltage']
run = selected['test_num']

model = models.Model(kind='reciprocal')
results = model.fit(voltage, weight)
x,y = model.get_line()
r2 = model.r2
parameters = model.parameters

#format r2 to text with 2 decimal places
r2_text = "{:.2f}".format(r2)

#format parameters to text with 2 decimal places
parameters_text = [ "{:.2f}".format(i) for i in parameters]
parameters_text = str(parameters_text)
parameters_text = parameters_text.replace("'","")

plt.figure()
plt.scatter(voltage, weight, c=run)
plt.plot(x, y, color='red')
plt.xlabel('Voltage')
plt.ylabel('Weight')
plt.title('Weight vs Voltage')
# add r2 to plot
plt.text(0.01, 0.925, '$R^2$: ' + r2_text, transform=plt.gca().transAxes)
plt.text(0.01, 0.9, '$parameters$: ' + parameters_text, transform=plt.gca().transAxes)
plt.show()

errors = results['errors']
print('mean of errors:', errors.mean())
print('std of errors:', errors.std())


plt.figure()
plt.hist(errors, bins=20)
plt.xlabel('Error')
plt.ylabel('Frequency')
plt.title('Error Distribution')
plt.show()

