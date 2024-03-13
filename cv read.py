import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

def read_csv_result(file_path):
    try:
        # Read the file with the appropriate handling for bad lines.
        # The 'on_bad_lines' parameter is set to 'skip' to ignore problematic lines.
        data = pd.read_csv(file_path, delimiter=',', skiprows=6,usecols=[1, 3, 5, 7], on_bad_lines='skip',encoding='utf-16')
        
        # Extract columns that contain 'µA' in their header after skipping the appropriate rows
        #current_data = data.filter(regex='µA').apply(pd.to_numeric, errors='coerce').dropna()
        return data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def determine_peak_current(data):
    # Find the peak current across all 'µA' columns
    peak_current = data.max().max()  # The highest current value across all scans
    return peak_current

# Use a raw string for the file path or double backslashes to avoid escape sequence issues
file_path = r'C:\Users\karla\Downloads\E2_CV_8nM.csv'  # Adjust this path as needed
data = read_csv_result(file_path)
# print(data)
peak_current = determine_peak_current(data)
# print(f"Peak current: {peak_current:.2f} µA")
def read_calibration_curve_csv(filename):
    # Read calibration curve data from CSV
    calibration_data = pd.read_csv(filename)
    concentration = calibration_data['Concentration']
    current_response = calibration_data['Current']
    return concentration, current_response

def calibration_function(concentration, current_response):
    current_response = current_response[2:]
    concentration = concentration[2:]
    # Interpolate the calibration curve data to obtain a function
    # Use the 'fill_value' parameter to allow extrapolation
    calibration_function = interp1d(concentration, current_response, kind='linear', fill_value='extrapolate')
    return calibration_function

print(peak_current)
data2 = read_calibration_curve_csv(r'C:\Users\karla\Downloads\Calibration_curve.csv')
concentration = data2[0]
current_response = data2[1]
function_cal = calibration_function(concentration, current_response)
print(function_cal(peak_current))
