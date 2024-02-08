import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

def read_data(file_path):
    """
    Read CV curve data from a text file.
    File format: 
    Potential(V)   Current(uA)
    """
    data = np.loadtxt(file_path)
    potential, current = data[:, 0], data[:, 1] # This to be changed depending on the file format given by the potentiostat
    return potential, current

def plot_cv_curve(potential, current):
    """
    Plot the cyclic voltammogram (CV) curve.
    """
    plt.figure()
    plt.plot(potential, current, marker='o', linestyle='-')
    plt.xlabel('Potential (V)')
    plt.ylabel('Current (uA)')
    plt.title('Cyclic Voltammogram (CV) Curve')
    plt.grid(True)
    plt.show()

def calibration_curve(x, *params):
    """
    Define a polynomial calibration curve for fitting.
    """
    return np.polyval(params, x)

def dual_frequency_calibration(potential, current):
    """
    Perform dual-frequency calibration.
    """
    # Fit a calibration to the CV data
    popt, _ = curve_fit(calibration_curve, potential, current)
    
    # Use the calibration curve to determine positive/negative outcome
    threshold = 0.0  # Adjust as needed, this is determined experimentally 
    # if the fitted curve at a certain potential is above a threshold, classify as positive, otherwise negative
    predicted_current = calibration_curve(potential, *popt)
    outcome = "positive" if np.any(predicted_current > threshold) else "negative"
    return outcome


