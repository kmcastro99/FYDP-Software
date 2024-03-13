import sys
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.stats import linregress
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox

class LODApp(QWidget):
    def __init__(self):
        super().__init__()
        self.cvFilePath = ""
        self.calibrationFilePath = ""
        self.setWindowTitle('LOD Calculator')
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Buttons
        self.loadCVButton = QPushButton('Load CV File', self)
        self.loadCVButton.clicked.connect(self.loadCVFile)

        self.loadCalibrationButton = QPushButton('Load Calibration File', self)
        self.loadCalibrationButton.clicked.connect(self.loadCalibrationFile)

        self.calculateButton = QPushButton('Calculate Result', self)
        self.calculateButton.clicked.connect(self.calculateResult)

        # Result label
        self.resultLabel = QLabel('Result: ', self)

        # Add widgets to layout
        layout.addWidget(self.loadCVButton)
        layout.addWidget(self.loadCalibrationButton)
        layout.addWidget(self.calculateButton)
        layout.addWidget(self.resultLabel)

    def loadCVFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Load CV File", "", "CSV Files (*.csv);;All Files (*)")
        if fileName:
            self.cvFilePath = fileName
            self.resultLabel.setText('CV File Loaded: ' + fileName.split('/')[-1])

    def loadCalibrationFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Calibration File", "", "CSV Files (*.csv);;All Files (*)")
        if fileName:
            self.calibrationFilePath = fileName
            self.resultLabel.setText('Calibration File Loaded: ' + fileName.split('/')[-1])

    def calculateResult(self):
        if self.cvFilePath and self.calibrationFilePath:
            try:
                # Process the CSV file and determine results
                amperometric_currents = self.read_csv_first_column(self.cvFilePath)
                current_values = amperometric_currents.iloc[3:]  # Only take numeric values
                
                calibration_concentration, calibration_current = self.read_calibration_curve(self.calibrationFilePath)
                calibration_func = self.create_calibration_function(calibration_concentration, calibration_current)

                # Determine the steady-state current and SNR for the amperometric data
                steady_state_current, snr = self.determine_steady_state_current(current_values)

                # Determine the limit of detection (LOD) based on the calibration function
                lod_concentration = self.calculate_lod_from_calibration(calibration_concentration, calibration_current)

                # Determine if the response is positive or negative based on the LOD
                overall_result = self.determine_result(calibration_func, steady_state_current, lod_concentration)

                self.resultLabel.setText(f"Overall result: {overall_result}")
            except Exception as e:
                QMessageBox.warning(self, "Calculation Error", "An error occurred during calculation: " + str(e))
        else:
            QMessageBox.warning(self, "File Missing", "Please load both CV and Calibration files before calculation.")

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

def main():
    app = QApplication(sys.argv)
    ex = LODApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
