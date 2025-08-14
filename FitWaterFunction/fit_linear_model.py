import pandas as pd
from library import models
from matplotlib import pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.regression.mixed_linear_model import MixedLM
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


data = pd.read_csv('data/sensor_measures.csv')
data.columns = data.columns.str.strip()
print(data.columns)
selected = data.query('tester in ["LV"]')
selected = selected.query('voltage < 2500')
selected = selected.query('weight > 50')
selected = selected.query('weight < 400')

for selected_run in range(1, 5):

    currently_selected = selected.query('test_num == @selected_run')

    weight = currently_selected['weight']
    voltage = currently_selected['voltage']
    run = currently_selected['test_num']

    model = models.Model(kind='linear')
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


#%% Run linear model on all data
model = ols('weight ~ voltage + C(test_num)', data=selected)
result = model.fit()
print(result.summary())

mixed_model = MixedLM(endog=selected['weight'], exog=sm.add_constant(selected['voltage']), groups=selected['test_num'])
result = mixed_model.fit()
print(result.summary())

#------------

coef = result.fe_params['voltage']
se = result.bse['voltage']
ci_95 = 1.96 * se  # for 95% confidence interval

# For any voltage change (delta_v)
delta_v = 20
lower_weight_change = delta_v * (coef - ci_95)
center_weight_change = delta_v * coef
upper_weight_change = delta_v * (coef + ci_95)
weight_change_range = upper_weight_change - lower_weight_change
print(lower_weight_change, center_weight_change, upper_weight_change, weight_change_range)
