
# import pandas as pd
# import models
# import utils
# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.optimize import curve_fit
#
# from models import square_model, free_model
#
# data = pd.read_csv('water_testing_10-21-24.csv')
# data = data.query('weight < 440')
# weight = data.weight.values
# voltage = data.voltage.values
#
# linear_model = models.linear_model
# square_model = models.square_model
# cubic_model = models.cubic_model
# free_model = models.free_model
#
# # Fit both models to the data
# linear_parameters, _ = curve_fit(linear_model, weight, voltage)
# square_parameters, _ = curve_fit(square_model, weight, voltage)
# cubic_parameters, _ = curve_fit(cubic_model, weight, voltage)
# free_parameters, _ = curve_fit(free_model, weight, voltage)
#
# # Generate predicted values for plotting
# vol_range = np.linspace(min(weight), max(weight), 100)  # Smooth range for plotting
# pred_ln = linear_model(vol_range, *linear_parameters)
# pred_sq = square_model(vol_range, *square_parameters)
# pred_cb = cubic_model(vol_range, *cubic_parameters)
# pred_fr = free_model(vol_range, *free_parameters)
#
# R2_sq = utils.calculate_r2(voltage, square_model(weight, *square_parameters))
# R2_cb = utils.calculate_r2(voltage, cubic_model(weight, *cubic_parameters))
# R2_fr = utils.calculate_r2(voltage, free_model(weight, *free_parameters))
#
# # Plot the data and both models
# plt.scatter(weight, voltage, color='black', label='Data', alpha=0.25)
# #plt.plot(vol_range, pred_ln, label=f'a * weight + b: a={linear_parameters[0]:.2f}, b={linear_parameters[1]:.2f}', color='blue')
# plt.plot(vol_range, pred_sq, label=f'a * weight^2 + b: a={square_parameters[0]:.2f}, b={square_parameters[1]:.2f}: R2={R2_sq:.2f}', color='blue')
# plt.plot(vol_range, pred_cb, label=f'a * weight^3 + b: a={cubic_parameters[0]:.2f}, b={cubic_parameters[1]:.2f}: R2={R2_cb:.2f}', color='red')
# plt.plot(vol_range, pred_fr, label=f'a * weight^c + b: a={free_parameters[0]:.2f}, b={free_parameters[1]:.2f}, c={free_parameters[2]:.2f}: R2={R2_fr:.2f}', color='purple')
# plt.xlabel('Weight')
# plt.ylabel('Sensor Reading')
# plt.legend()
# plt.grid()
# plt.show()

