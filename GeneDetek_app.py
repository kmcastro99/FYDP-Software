import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.stats import linregress
import base64
import requests

def read_calibration_curve_csv(filename):
    # Read calibration curve data from CSV
    try:
        calibration_data = pd.read_csv(filename)
        calibration_data = pd.read_csv(filename)
        concentration = calibration_data['Concentration']
        current_response = calibration_data['Current']
        return concentration, current_response
    except Exception as e:
        st.error(f"Error reading {filename}: {e}")
        return None

def create_calibration_function(concentration, current_response):
    # Interpolate the calibration curve data to obtain a function
    # Use the 'fill_value' parameter to allow extrapolation
    calibration_function = interp1d(current_response, concentration, kind='linear', fill_value='extrapolate')
    
    return calibration_function

def plot_calibration_curve(concentration, current_response):
    # Plot the calibration curve and the interpolation function
    fig, ax = plt.subplots()
    ax.scatter(concentration, current_response, color='blue', label='Calibration data')
    ax.set_xlabel('Concentration (nM)')
    ax.set_ylabel('Current (nA)')
    ax.legend()
    return fig

def read_csv_result(file_path):
    # Read the CSV file with UTF-16 encoding and flexible handling of inconsistencies
    df = pd.read_csv(file_path, encoding='utf-16', sep=',', on_bad_lines='skip', engine='python')
    # Skip the rows that are not numeric
    numeric_data = pd.to_numeric(df.iloc[:, 1], errors='coerce')
    # Drop NaN values that result from coercion errors (i.e., non-numeric data)
    numeric_data = numeric_data.dropna().reset_index(drop=True)

    return numeric_data

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
    slope, intercept, r_value, p_value, std_err = linregress(concentration, current_response)
    # Calculate the standard deviation of the response (σ) at the lowest concentration
    std_response =  np.std(current_response[concentration == 0])
    # Calculate the LOD using the 3.3σ/S formula
    lod = 3.3 * std_response / slope
    return lod


def determine_result(calibration_function, steady_state_current, lod_concentration):
    # Determine if the steady-state current corresponds to a concentration above the LOD
    concentration = calibration_function(steady_state_current)
    result = "Positive" if concentration >= lod_concentration else "Negative"
    return result

# Process calibration file
#new_path = r'C:\Users\karla\OneDrive\Documents\NE 4B\NE 409\FYDP-Software'
calibration_file_path = 'data/Calibration_curve.csv'
calibration_concentration, calibration_current = read_calibration_curve_csv(calibration_file_path)
doc_url = 'https://github.com/kmcastro99/FYDP-Software/blob/388595c03638b3932c6110368186b42ae759769a/Report/Report_Positive.docx'
doc_name = 'Report_Positive.docx'
# Streamlit app
def main():
    st.set_page_config(page_title="GeneDetek",page_icon=":dna:",layout="centered")
    st.title("GeneDetek :dna:")
    st.write("")
    st.write("We are supporting personalized medicine for depression treatment: Your Gene, Your Medicine")
    st.write("")
    st.write("")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Calibration Curve')
        fig = plot_calibration_curve(calibration_concentration, calibration_current)
        st.pyplot(fig)

    with col2:
        st.subheader('Limit of Detection (LOD)')
        lod_concentration = calculate_lod_from_calibration(calibration_concentration, calibration_current)
        st.write(f"Our Sensor has a LOD of: {round(lod_concentration,2)} nM")

    # File uploader allows the user to upload CSV files
    st.write("")
    st.write("")
    st.subheader('Analysis of Results')
    st.write("Please upload the CSV file with the amperometric results to analyze.")
    cv_file = st.file_uploader("Upload Amperometric CSV", type=['csv'])

    if cv_file:
        if st.button('Calculate Result'):
            # Process CV file
            amperometric_currents = read_csv_result(cv_file)
            current_values = amperometric_currents.iloc[3:]  # Only take numeric values
            
            calibration_func = create_calibration_function(calibration_concentration, calibration_current)

            # Determine steady-state current and SNR
            steady_state_current, snr = determine_steady_state_current(current_values)
            
            # Determine result
            overall_result = determine_result(calibration_func, steady_state_current, lod_concentration)
            
            # Display result
            if overall_result == "Positive":
                st.error(f"{overall_result}")
            else:
                st.success(f"{overall_result}")
        else:
            st.write("Upload a CSV file with the results to enable the 'Calculate Result' button.")

    st.subheader("Report Generation")
    st.write("")
    st.write("")
    st.write("Please, enter the following data to generate the report:")
    st.write("")
    collection_date = st.text_input("Collection Date")
    patient_id = st.text_input("Patient ID")
    patient_name = st.text_input("Patient Name")
    age = st.text_input("Age")
    gender = st.text_input("Gender")

    if st.button("Generate Report"):
        if collection_date == "" or patient_id == "" or patient_name == "" or age == "" or gender == "":
            st.error("Please enter the missing information")
        else:
            st.write("Generating report...")
            st.write("Report generated successfully!")
            st.write("Download the report below.")
            if st.button("Download Report"):
                r = requests.get(doc_url)
                if r.status_code == 200:
                    st.download_button(
                        label="Download Report",
                        data=r.content,
                        file_name=doc_name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                else:
                    st.error("Failed to download the report.")
                

if __name__ == '__main__':
    main()