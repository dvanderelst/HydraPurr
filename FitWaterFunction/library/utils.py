import numpy as np


def calculate_r2(actual, predicted):
    """
    Calculate the coefficient of determination (R^2) for a model.

    Parameters:
    - actual (array-like): The actual observed values.
    - predicted (array-like): The predicted values from the model.

    Returns:
    - float: The R^2 value.
    """
    # Convert inputs to numpy arrays for consistency
    actual = np.array(actual)
    predicted = np.array(predicted)
    # Calculate RSS (Residual Sum of Squares)
    rss = np.sum((actual - predicted) ** 2)
    # Calculate TSS (Total Sum of Squares)
    tss = np.sum((actual - np.mean(actual)) ** 2)
    errors = predicted - actual
    # Calculate R^2
    r2 = 1 - (rss / tss)
    return r2, errors