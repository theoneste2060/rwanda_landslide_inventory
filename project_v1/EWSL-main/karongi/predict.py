import os
import pandas as pd
import numpy as np
import time
import joblib
import warnings
import shutil
from datetime import datetime

# Load the trained model and label encoders
model = joblib.load('karongi/karongi.pkl')
label_encoders = joblib.load('karongi/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def decode_categorical(data_row):
    # Decode categorical data
    categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for col in categorical_cols:
        label_encoder = label_encoders[col]
        data_row[col] = label_encoder.inverse_transform([data_row[col]])[0]
    return data_row


# Function to perform prediction
def predict_landslide(data_row):
    # Encode categorical data
    categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for col in categorical_cols:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            data_row[col] = label_encoders[col].transform([data_row[col]])[0]
    
    # Remove the last two columns
    data_row = data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    probability = model.predict_proba(data_row.values.reshape(1, -1))[0]
    return probability, data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def predict_landslide_occurrence(file_path):
    global predicted_results
    while True:
        # Load CSV file
        data = pd.read_csv(file_path)
        num_rows = len(data)
        
        # Iterate through each row
        for i in range(num_rows):
            row_data = data.iloc[i]
            longitude = row_data['Longitude']
            latitude = row_data['Latitude']
            probability, input_data = predict_landslide(row_data)
            
            landslide_probability = probability[1] * 100  # Probability of landslide
            
            print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            input_data_decoded = decode_categorical(input_data)
            
            # Append the predicted results to the DataFrame
            new_row = {'Longitude': longitude,
                       'Latitude': latitude,
                       **input_data_decoded.to_dict(),
                       'Landslide_Probability': landslide_probability}
            predicted_results = pd.concat([predicted_results, pd.DataFrame([new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            predicted_results.to_csv('karongi/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('karongi/predicted_results.csv') and os.path.getsize('karongi/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('karongi/archive'):
                    os.makedirs('karongi/archive')
                # Append timestamp to the copied file name
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                archive_file_name = f'karongi/archive/predicted_results_copy_{timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('karongi/predicted_results.csv', archive_file_name)
                # Reinitialize the predicted_results DataFrame
                predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if i == num_rows - 1:
                print("Reached the last row. Starting from the beginning.")
                break

# Call the function to predict landslide occurrence
predict_landslide_occurrence('karongi/karongi_inputs.csv')
