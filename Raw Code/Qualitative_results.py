import os
import numpy as np
import pandas as pd
import scipy.stats
from scipy.interpolate import interp1d
import streamlit as st


def read_csv_first_column(file_path):

    # Read the CSV file with UTF-16 encoding and flexible handling of inconsistencies
    df = pd.read_csv(file_path, encoding='utf-16', sep=',', on_bad_lines='skip', engine='python')
    
    # Skip the rows that are not numeric
    numeric_data = pd.to_numeric(df.iloc[:, 1], errors='coerce')
    
    # Drop NaN values that result from coercion errors (i.e., non-numeric data)
    numeric_data = numeric_data.dropna().reset_index(drop=True)
    
    return numeric_data

def read_calibration_curve(filename):
    # Read calibration curve data from CSV
    calibration_data = pd.read_csv(filename)
    concentration = calibration_data['Concentration']
    current_response = calibration_data['Current']
    
    return concentration, current_response

def create_calibration_function(concentration, current_response):
    # Interpolate the calibration curve data to obtain a function
    # Use the 'fill_value' parameter to allow extrapolation
    calibration_function = interp1d(current_response, concentration, kind='linear', fill_value="extrapolate")
    
    return calibration_function

def determine_steady_state_current(amperometric_data, window_size=10):
    # Calculate the moving average to smooth out the data
    moving_avg = amperometric_data.rolling(window=window_size).mean()

    # Determine the steady-state current as the average of the last few points
    steady_state_current = moving_avg.iloc[-window_size:].mean()

    # Calculate the standard deviation of the last few points as a measure of noise
    noise = amperometric_data.iloc[-window_size:].std()

    # Calculate the signal-to-noise ratio (SNR)
    snr = steady_state_current / noise if noise > 0 else np.inf

    return steady_state_current, snr

def calculate_lod_from_calibration(concentration, current_response):
    # Perform a linear regression to get the slope (S) and intercept
    slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(concentration, current_response)
    print(slope)
    print(std_err)
    print(intercept)
    print(r_value)
    # Calculate the standard deviation of the response (σ) at the lowest concentration
    std_response =  np.std(current_response[concentration == 0])
    print(std_response)
    
    # Calculate the LOD using the 3.3σ/S formula
    lod = 3.3 * std_err / slope
    return lod


def determine_result(calibration_function, steady_state_current, lod_concentration):
    # Determine if the steady-state current corresponds to a concentration above the LOD
    concentration = calibration_function(steady_state_current)
    result = "Positive" if concentration >= lod_concentration else "Negative"
    return result


# Example usage
# Define the new path and change the working directory
new_path = r'C:\Users\karla\OneDrive\Documents\NE 4B\NE 409\FYDP-Software'
os.chdir(new_path)

# Process the CSV file and determine results
file_path = 'E5_Amp0.4_0nM.csv'
amperometric_currents = read_csv_first_column(file_path)
current_values = amperometric_currents.iloc[3:]  # Only take numeric values
calibration_concentration, calibration_current = read_calibration_curve('calibration_curve.csv')
calibration_func = create_calibration_function(calibration_concentration, calibration_current)

# Determine the steady-state current and SNR for the amperometric data
steady_state_current, snr = determine_steady_state_current(current_values)
print("Steady-state current:", steady_state_current)
print("Signal-to-noise ratio (SNR):", snr)

# Determine the limit of detection (LOD) based on the calibration function
lod_concentration = calculate_lod_from_calibration(calibration_concentration, calibration_current)
print("Limit of detection (LOD):", lod_concentration)

# Determine if the response is positive or negative based on the LOD
overall_result = determine_result(calibration_func, steady_state_current, lod_concentration)
print("Overall result:", overall_result)
