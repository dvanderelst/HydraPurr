# Define the models
# a is a scaling parameter, b is an offset parameter
from logging import error
from wsgiref.util import request_uri

from scipy.optimize import curve_fit
from library import utils
import numpy as np
from matplotlib import pyplot as plt

def log_model(independent, a, b):
    return a * np.log(independent) + b

def linear_model(independent, a, b):
    return a * independent + b

def square_model(independent, a, b):
    return a * (independent**2) + b

def cubic_model(independent, a, b):
    return a * (independent**3) + b

def free_model(independent, a, b, c):
    return a * (independent**c) + b

def reciprocal_model(independent, a, b, c):
    return a / (independent ** c) + b


class Model:
    def __init__(self, kind):
        self.model = None
        self.parameters = None
        self.independent = None
        self.dependent = None
        self.r2 = None
        self.kind = kind
        if kind == 'log': self.model = log_model
        if kind == 'linear': self.model = linear_model
        if kind == 'square': self.model = square_model
        if kind == 'cubic': self.model = cubic_model
        if kind == 'free': self.model = free_model
        if kind == 'reciprocal': self.model = reciprocal_model

    def fit(self, independent, dependent):
        independent = np.array(independent)
        dependent = np.array(dependent)
        not_nans = ~np.isnan(independent) * ~np.isnan(dependent)
        independent = independent[not_nans]
        dependent = dependent[not_nans]
        self.dependent = dependent
        self.independent = independent

        if self.kind == 'free':
            p0 = [1, 1, 1]
            bounds = ([-np.inf, -np.inf, 0.1], [np.inf, np.inf, 3])
            fit_result = curve_fit(self.model, independent, dependent, p0=p0, bounds=bounds, maxfev=10000)
        elif self.kind == 'reciprocal':
            p0 = [1, 1, 1]
            bounds = ([-np.inf, -np.inf, 0.1], [np.inf, np.inf, 3])
            fit_result = curve_fit(self.model, independent, dependent, p0=p0, bounds=bounds, maxfev=10000)
        else:
            fit_result = curve_fit(self.model, independent, dependent, maxfev=10000)
        self.parameters = fit_result[0]

        prediction = self.predict()
        r2, errors = utils.calculate_r2(dependent, prediction)
        self.r2 = r2
        results= {}
        results['r2'] = r2
        results['parameters'] = self.parameters
        results['errors'] = errors
        return results


    def get_line(self):
        minimum = np.min(self.independent)
        maximum = np.max(self.independent)
        fitted_range = np.linspace(minimum, maximum, 1000)
        y = self.model(fitted_range, *self.parameters)
        return fitted_range, y

    def predict(self):
        return self.model(self.independent, *self.parameters)









