import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.stats import linregress, t
import requests
import datetime

def read_calibration_curve_csv(filename):
    # Read calibration curve data from CSV
    try:
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
    current_response = current_response[1:]# To get only one zero value
    concentration = concentration[1:]# To get only one zero value
    # Fit a linear regression model
    slope, intercept, r_value, p_value, std_err = linregress(concentration, current_response)
    # Create a function using the slope and intercept
    calibration_function = lambda y: (y - intercept)/y
    
    return calibration_function, slope, intercept, r_value, std_err

def plot_calibration_curve(concentration, current_response):
    # Fit the calibration curve
    calibration_function, slope, intercept, r_value, std_err = create_calibration_function(concentration, current_response)

    # Generate points for the fitted line
    x_fit = np.linspace(concentration.min(), concentration.max(), 100)
    y_fit = np.linspace(current_response.min(), current_response.max(), 100)

    # Plot the calibration data
    fig, ax = plt.subplots()
    ax.scatter(concentration[1:], current_response[1:], color='cornflowerblue', label='Calibration data')
    #ax.plot(concentration[1:], current_response[1:], color='blue')
    ax.plot(x_fit, y_fit, color='royalblue', label='Fitted line')

    # Annotation with calibration function and statistics
    textstr = f'y = {slope:.2f}x + {intercept:.2f}\n$R^2 = {r_value**2:.2f}$'
    props = dict(boxstyle='round', facecolor='white', alpha=0.5)
    ax.text(0.75, 0.10, textstr, transform=ax.transAxes, fontsize=9,
            verticalalignment='center', bbox=props)

    # Labeling
    ax.set_xlabel('Concentration (nM)')
    ax.set_ylabel('Current (uA)')
    ax.legend()
    ax.grid(False)

    return fig

# Read CSV for CV data
def read_csv_result(file_path):
    try:
        # Read the file with the appropriate handling for bad lines.
        # The 'on_bad_lines' parameter is set to 'skip' to ignore problematic lines.
        data = pd.read_csv(file_path, delimiter=',', skiprows=6,usecols=[1, 3, 5, 7], on_bad_lines='skip',encoding='utf-16')
        return data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Used to determine peak in CV data
def determine_peak_current(data):
    # Find the peak current across all 'µA' columns
    peak_current = data.max().max()  # The highest current value across all scans
    return peak_current

def calculate_lod_from_calibration(concentration, current_response):
    # Perform a linear regression to get the slope (S) and intercept
    calibration_function, slope, intercept, r_value, std_err = create_calibration_function(concentration, current_response)
    # Calculate the standard deviation of the response (σ) at the lowest concentration
    std_response =  np.std(current_response[concentration == 0])
    # Calculate the LOD using the 3.3σ/S formula
    lod = 3.3 * (std_response / slope)
    return lod, slope, std_response


def determine_result(calibration_function, peak_current, lod_concentration):
    # Determine if the steady-state current corresponds to a concentration above the LOD
    concentration = calibration_function(peak_current)
    result = "Positive" if concentration >= lod_concentration else "Negative"
    return result

# Process calibration file
#new_path = r'C:\Users\karla\OneDrive\Documents\NE 4B\NE 409\FYDP-Software'
calibration_file_path = 'data/Calibration_curve.csv'
calibration_concentration, calibration_current = read_calibration_curve_csv(calibration_file_path)
doc_url = 'https://github.com/kmcastro99/FYDP-Software/raw/388595c03638b3932c6110368186b42ae759769a/Report/Report_Positive.docx'
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
        lod_concentration,slope, std_response = calculate_lod_from_calibration(calibration_concentration, calibration_current)
        st.write(f"The GeneDetek Sensor has a LOD of: {round(lod_concentration,3)} nM")
        st.write(f"The slope of the calibration curve is: {round(slope,3)}")
        st.write(f"The standard deviation of the response at the lowest concentrations is: {round(std_response,3)}")

    # File uploader allows the user to upload CSV files
    st.write("")
    st.write("")
    st.subheader('Analysis of Results')
    st.write("Please upload the CSV file with the results to analyze.")
    cv_file = st.file_uploader("Upload CV CSV with results", type=['csv'])

    if cv_file:
        if st.button('Calculate Result'):
            # Process CV file
            result_currents = read_csv_result(cv_file)
            # current_values = result_currents.iloc[5:]
            calibration_func, slope, intercept, r_value, std_err = create_calibration_function(calibration_concentration, calibration_current)

            # Determine steady-state current and SNR
            # steady_state_current, snr = determine_steady_state_current(current_values)
            peak_current = determine_peak_current(result_currents)
            # Determine result
            overall_result = determine_result(calibration_func, peak_current, lod_concentration)
            st.write(f"Peak current: {peak_current:.2f} µA")
            st.write(f"Concentration: {calibration_func(peak_current):.2f} nM")
            # Display result
            if overall_result == "Positive":
                st.success(f"{overall_result}")
            else:
                st.error(f"{overall_result}")
        else:
            st.write("Upload a CSV file with the results to enable the 'Calculate Result' button.")

    st.subheader("Report Generation")
    st.write("")
    st.write("")
    st.write("Please, enter the following data to generate the report:")
    st.write("")
    collection_date = st.date_input("Collection Date", datetime.date(2024, 3, 13))
    patient_id = st.text_input("Patient ID")
    patient_name = st.text_input("Patient Name")
    age = st.text_input("Age")
    gender = st.text_input("Gender")

    if st.button("Generate Report"):
        if patient_id == "" or patient_name == "" or age == "" or gender == "":
            st.error("Please enter the missing information")
        else:
            st.write("Generating report...")
            st.write("Report generated successfully!")
            st.write("Download the report below.")
            r = requests.get(doc_url, stream=True)
            if r.status_code == 200:
                st.download_button(
                label="Download Report",
                data=r.content,
                file_name=doc_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            else:
                st.error("Failed to download the report.")
    
    st.write("")
    st.write("")
    st.write("")
    st.image("./GeneDetek.png")
    st.write("GeneDetek is a product of GeneDetek Inc. All rights reserved.")

if __name__ == '__main__':
    main()