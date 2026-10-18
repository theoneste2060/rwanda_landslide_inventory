import warnings
from flask import Flask, jsonify, render_template, request, send_from_directory, flash, redirect, session, url_for
import csv
import os.path
import time
import traceback

import os
import pandas as pd
import numpy as np
import time
import joblib
import warnings
import shutil
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key'



# Load the trained model and label encoders
rutsiro_model = joblib.load('rutsiro/rutsiro.pkl')
rutsiro_label_encoders = joblib.load('rutsiro/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
rutsiro_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *rutsiro_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def rutsiro_decode_categorical(rutsiro_data_row):
    # Decode categorical data
    rutsiro_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for rutsiro_col in rutsiro_categorical_cols:
        rutsiro_label_encoder = rutsiro_label_encoders[rutsiro_col]
        rutsiro_data_row[rutsiro_col] = rutsiro_label_encoder.inverse_transform([rutsiro_data_row[rutsiro_col]])[0]
    return rutsiro_data_row

# Function to perform prediction
def rutsiro_predict_landslide(rutsiro_data_row):
    # Encode categorical data
    rutsiro_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for rutsiro_col in rutsiro_categorical_cols:
        rutsiro_data_row[rutsiro_col] = rutsiro_label_encoders[rutsiro_col].transform([rutsiro_data_row[rutsiro_col]])[0]
    
    # Remove the last two columns
    rutsiro_data_row = rutsiro_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    rutsiro_probability = rutsiro_model.predict_proba(rutsiro_data_row.values.reshape(1, -1))[0]
    return rutsiro_probability, rutsiro_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def rutsiro_predict_landslide_occurrence(rutsiro_file_path):
    global rutsiro_predicted_results
    while True:
        # Load CSV file
        rutsiro_data = pd.read_csv(rutsiro_file_path)
        rutsiro_num_rows = len(rutsiro_data)
        
        # Iterate through each row
        for rutsiro_i in range(rutsiro_num_rows):
            rutsiro_row_data = rutsiro_data.iloc[rutsiro_i]
            rutsiro_longitude = rutsiro_row_data['Longitude']
            rutsiro_latitude = rutsiro_row_data['Latitude']
            rutsiro_probability, rutsiro_input_data = rutsiro_predict_landslide(rutsiro_row_data)
            
            rutsiro_landslide_probability = rutsiro_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            rutsiro_input_data_decoded = rutsiro_decode_categorical(rutsiro_input_data)
            
            # Append the predicted results to the DataFrame
            rutsiro_new_row = {'Longitude': rutsiro_longitude,
                                 'Latitude': rutsiro_latitude,
                                 **rutsiro_input_data_decoded.to_dict(),
                                 'Landslide_Probability': rutsiro_landslide_probability}
            rutsiro_predicted_results = pd.concat([rutsiro_predicted_results, pd.DataFrame([rutsiro_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            rutsiro_predicted_results.to_csv('rutsiro/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('rutsiro/predicted_results.csv') and os.path.getsize('rutsiro/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('rutsiro/archive'):
                    os.makedirs('rutsiro/archive')
                # Append timestamp to the copied file name
                rutsiro_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                rutsiro_archive_file_name = f'rutsiro/archive/predicted_results_copy_{rutsiro_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('rutsiro/predicted_results.csv', rutsiro_archive_file_name)
                # Reinitialize the rutsiro_predicted_results DataFrame
                rutsiro_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *rutsiro_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if rutsiro_i == rutsiro_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/rutsiropredict')
def rutsiro_predict():
    rutsiro_file_path = 'rutsiro/rutsiro_inputs.csv'
    rutsiro_predict_landslide_occurrence(rutsiro_file_path)
    return redirect(url_for('Rutsiro'))


# Load the trained model and label encoders
rusizi_model = joblib.load('rusizi/rusizi.pkl')
rusizi_label_encoders = joblib.load('rusizi/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
rusizi_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *rusizi_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def rusizi_decode_categorical(rusizi_data_row):
    # Decode categorical data
    rusizi_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for rusizi_col in rusizi_categorical_cols:
        rusizi_label_encoder = rusizi_label_encoders[rusizi_col]
        rusizi_data_row[rusizi_col] = rusizi_label_encoder.inverse_transform([rusizi_data_row[rusizi_col]])[0]
    return rusizi_data_row

# Function to perform prediction
def rusizi_predict_landslide(rusizi_data_row):
    # Encode categorical data
    rusizi_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for rusizi_col in rusizi_categorical_cols:
        rusizi_data_row[rusizi_col] = rusizi_label_encoders[rusizi_col].transform([rusizi_data_row[rusizi_col]])[0]
    
    # Remove the last two columns
    rusizi_data_row = rusizi_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    rusizi_probability = rusizi_model.predict_proba(rusizi_data_row.values.reshape(1, -1))[0]
    return rusizi_probability, rusizi_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def rusizi_predict_landslide_occurrence(rusizi_file_path):
    global rusizi_predicted_results
    while True:
        # Load CSV file
        rusizi_data = pd.read_csv(rusizi_file_path)
        rusizi_num_rows = len(rusizi_data)
        
        # Iterate through each row
        for rusizi_i in range(rusizi_num_rows):
            rusizi_row_data = rusizi_data.iloc[rusizi_i]
            rusizi_longitude = rusizi_row_data['Longitude']
            rusizi_latitude = rusizi_row_data['Latitude']
            rusizi_probability, rusizi_input_data = rusizi_predict_landslide(rusizi_row_data)
            
            rusizi_landslide_probability = rusizi_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            rusizi_input_data_decoded = rusizi_decode_categorical(rusizi_input_data)
            
            # Append the predicted results to the DataFrame
            rusizi_new_row = {'Longitude': rusizi_longitude,
                                 'Latitude': rusizi_latitude,
                                 **rusizi_input_data_decoded.to_dict(),
                                 'Landslide_Probability': rusizi_landslide_probability}
            rusizi_predicted_results = pd.concat([rusizi_predicted_results, pd.DataFrame([rusizi_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            rusizi_predicted_results.to_csv('rusizi/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('rusizi/predicted_results.csv') and os.path.getsize('rusizi/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('rusizi/archive'):
                    os.makedirs('rusizi/archive')
                # Append timestamp to the copied file name
                rusizi_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                rusizi_archive_file_name = f'rusizi/archive/predicted_results_copy_{rusizi_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('rusizi/predicted_results.csv', rusizi_archive_file_name)
                # Reinitialize the rusizi_predicted_results DataFrame
                rusizi_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *rusizi_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if rusizi_i == rusizi_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/rusizipredict')
def rusizi_predict():
    rusizi_file_path = 'rusizi/rusizi_inputs.csv'
    rusizi_predict_landslide_occurrence(rusizi_file_path)
    return redirect(url_for('Rusizi'))



# Load the trained model and label encoders
rulindo_model = joblib.load('rulindo/rulindo.pkl')
rulindo_label_encoders = joblib.load('rulindo/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
rulindo_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *rulindo_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def rulindo_decode_categorical(rulindo_data_row):
    # Decode categorical data
    rulindo_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for rulindo_col in rulindo_categorical_cols:
        rulindo_label_encoder = rulindo_label_encoders[rulindo_col]
        rulindo_data_row[rulindo_col] = rulindo_label_encoder.inverse_transform([rulindo_data_row[rulindo_col]])[0]
    return rulindo_data_row

# Function to perform prediction
def rulindo_predict_landslide(rulindo_data_row):
    # Encode categorical data
    rulindo_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for rulindo_col in rulindo_categorical_cols:
        rulindo_data_row[rulindo_col] = rulindo_label_encoders[rulindo_col].transform([rulindo_data_row[rulindo_col]])[0]
    
    # Remove the last two columns
    rulindo_data_row = rulindo_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    rulindo_probability = rulindo_model.predict_proba(rulindo_data_row.values.reshape(1, -1))[0]
    return rulindo_probability, rulindo_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def rulindo_predict_landslide_occurrence(rulindo_file_path):
    global rulindo_predicted_results
    while True:
        # Load CSV file
        rulindo_data = pd.read_csv(rulindo_file_path)
        rulindo_num_rows = len(rulindo_data)
        
        # Iterate through each row
        for rulindo_i in range(rulindo_num_rows):
            rulindo_row_data = rulindo_data.iloc[rulindo_i]
            rulindo_longitude = rulindo_row_data['Longitude']
            rulindo_latitude = rulindo_row_data['Latitude']
            rulindo_probability, rulindo_input_data = rulindo_predict_landslide(rulindo_row_data)
            
            rulindo_landslide_probability = rulindo_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            rulindo_input_data_decoded = rulindo_decode_categorical(rulindo_input_data)
            
            # Append the predicted results to the DataFrame
            rulindo_new_row = {'Longitude': rulindo_longitude,
                                 'Latitude': rulindo_latitude,
                                 **rulindo_input_data_decoded.to_dict(),
                                 'Landslide_Probability': rulindo_landslide_probability}
            rulindo_predicted_results = pd.concat([rulindo_predicted_results, pd.DataFrame([rulindo_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            rulindo_predicted_results.to_csv('rulindo/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('rulindo/predicted_results.csv') and os.path.getsize('rulindo/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('rulindo/archive'):
                    os.makedirs('rulindo/archive')
                # Append timestamp to the copied file name
                rulindo_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                rulindo_archive_file_name = f'rulindo/archive/predicted_results_copy_{rulindo_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('rulindo/predicted_results.csv', rulindo_archive_file_name)
                # Reinitialize the rulindo_predicted_results DataFrame
                rulindo_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *rulindo_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if rulindo_i == rulindo_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/rulindopredict')
def rulindo_predict():
    rulindo_file_path = 'rulindo/rulindo_inputs.csv'
    rulindo_predict_landslide_occurrence(rulindo_file_path)
    return redirect(url_for('Rulindo'))



# Load the trained model and label encoders
rubavu_model = joblib.load('rubavu/rubavu.pkl')
rubavu_label_encoders = joblib.load('rubavu/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
rubavu_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *rubavu_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def rubavu_decode_categorical(rubavu_data_row):
    # Decode categorical data
    rubavu_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for rubavu_col in rubavu_categorical_cols:
        rubavu_label_encoder = rubavu_label_encoders[rubavu_col]
        rubavu_data_row[rubavu_col] = rubavu_label_encoder.inverse_transform([rubavu_data_row[rubavu_col]])[0]
    return rubavu_data_row

# Function to perform prediction
def rubavu_predict_landslide(rubavu_data_row):
    # Encode categorical data
    rubavu_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for rubavu_col in rubavu_categorical_cols:
        rubavu_data_row[rubavu_col] = rubavu_label_encoders[rubavu_col].transform([rubavu_data_row[rubavu_col]])[0]
    
    # Remove the last two columns
    rubavu_data_row = rubavu_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    rubavu_probability = rubavu_model.predict_proba(rubavu_data_row.values.reshape(1, -1))[0]
    return rubavu_probability, rubavu_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def rubavu_predict_landslide_occurrence(rubavu_file_path):
    global rubavu_predicted_results
    while True:
        # Load CSV file
        rubavu_data = pd.read_csv(rubavu_file_path)
        rubavu_num_rows = len(rubavu_data)
        
        # Iterate through each row
        for rubavu_i in range(rubavu_num_rows):
            rubavu_row_data = rubavu_data.iloc[rubavu_i]
            rubavu_longitude = rubavu_row_data['Longitude']
            rubavu_latitude = rubavu_row_data['Latitude']
            rubavu_probability, rubavu_input_data = rubavu_predict_landslide(rubavu_row_data)
            
            rubavu_landslide_probability = rubavu_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            rubavu_input_data_decoded = rubavu_decode_categorical(rubavu_input_data)
            
            # Append the predicted results to the DataFrame
            rubavu_new_row = {'Longitude': rubavu_longitude,
                                 'Latitude': rubavu_latitude,
                                 **rubavu_input_data_decoded.to_dict(),
                                 'Landslide_Probability': rubavu_landslide_probability}
            rubavu_predicted_results = pd.concat([rubavu_predicted_results, pd.DataFrame([rubavu_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            rubavu_predicted_results.to_csv('rubavu/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('rubavu/predicted_results.csv') and os.path.getsize('rubavu/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('rubavu/archive'):
                    os.makedirs('rubavu/archive')
                # Append timestamp to the copied file name
                rubavu_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                rubavu_archive_file_name = f'rubavu/archive/predicted_results_copy_{rubavu_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('rubavu/predicted_results.csv', rubavu_archive_file_name)
                # Reinitialize the rubavu_predicted_results DataFrame
                rubavu_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *rubavu_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if rubavu_i == rubavu_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/rubavupredict')
def rubavu_predict():
    rubavu_file_path = 'rubavu/rubavu_inputs.csv'
    rubavu_predict_landslide_occurrence(rubavu_file_path)
    return redirect(url_for('Rubavu'))



# Load the trained model and label encoders
nyamasheke_model = joblib.load('nyamasheke/nyamasheke.pkl')
nyamasheke_label_encoders = joblib.load('nyamasheke/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
nyamasheke_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *nyamasheke_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def nyamasheke_decode_categorical(nyamasheke_data_row):
    # Decode categorical data
    nyamasheke_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for nyamasheke_col in nyamasheke_categorical_cols:
        nyamasheke_label_encoder = nyamasheke_label_encoders[nyamasheke_col]
        nyamasheke_data_row[nyamasheke_col] = nyamasheke_label_encoder.inverse_transform([nyamasheke_data_row[nyamasheke_col]])[0]
    return nyamasheke_data_row

# Function to perform prediction
def nyamasheke_predict_landslide(nyamasheke_data_row):
    # Encode categorical data
    nyamasheke_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for nyamasheke_col in nyamasheke_categorical_cols:
        nyamasheke_data_row[nyamasheke_col] = nyamasheke_label_encoders[nyamasheke_col].transform([nyamasheke_data_row[nyamasheke_col]])[0]
    
    # Remove the last two columns
    nyamasheke_data_row = nyamasheke_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    nyamasheke_probability = nyamasheke_model.predict_proba(nyamasheke_data_row.values.reshape(1, -1))[0]
    return nyamasheke_probability, nyamasheke_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def nyamasheke_predict_landslide_occurrence(nyamasheke_file_path):
    global nyamasheke_predicted_results
    while True:
        # Load CSV file
        nyamasheke_data = pd.read_csv(nyamasheke_file_path)
        nyamasheke_num_rows = len(nyamasheke_data)
        
        # Iterate through each row
        for nyamasheke_i in range(nyamasheke_num_rows):
            nyamasheke_row_data = nyamasheke_data.iloc[nyamasheke_i]
            nyamasheke_longitude = nyamasheke_row_data['Longitude']
            nyamasheke_latitude = nyamasheke_row_data['Latitude']
            nyamasheke_probability, nyamasheke_input_data = nyamasheke_predict_landslide(nyamasheke_row_data)
            
            nyamasheke_landslide_probability = nyamasheke_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            nyamasheke_input_data_decoded = nyamasheke_decode_categorical(nyamasheke_input_data)
            
            # Append the predicted results to the DataFrame
            nyamasheke_new_row = {'Longitude': nyamasheke_longitude,
                                 'Latitude': nyamasheke_latitude,
                                 **nyamasheke_input_data_decoded.to_dict(),
                                 'Landslide_Probability': nyamasheke_landslide_probability}
            nyamasheke_predicted_results = pd.concat([nyamasheke_predicted_results, pd.DataFrame([nyamasheke_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            nyamasheke_predicted_results.to_csv('nyamasheke/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('nyamasheke/predicted_results.csv') and os.path.getsize('nyamasheke/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('nyamasheke/archive'):
                    os.makedirs('nyamasheke/archive')
                # Append timestamp to the copied file name
                nyamasheke_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                nyamasheke_archive_file_name = f'nyamasheke/archive/predicted_results_copy_{nyamasheke_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('nyamasheke/predicted_results.csv', nyamasheke_archive_file_name)
                # Reinitialize the nyamasheke_predicted_results DataFrame
                nyamasheke_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *nyamasheke_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if nyamasheke_i == nyamasheke_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/nyamashekepredict')
def nyamasheke_predict():
    nyamasheke_file_path = 'nyamasheke/nyamasheke_inputs.csv'
    nyamasheke_predict_landslide_occurrence(nyamasheke_file_path)
    return redirect(url_for('Nyamasheke'))



# Load the trained model and label encoders
nyamagabe_model = joblib.load('nyamagabe/nyamagabe.pkl')
nyamagabe_label_encoders = joblib.load('nyamagabe/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
nyamagabe_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *nyamagabe_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def nyamagabe_decode_categorical(nyamagabe_data_row):
    # Decode categorical data
    nyamagabe_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for nyamagabe_col in nyamagabe_categorical_cols:
        nyamagabe_label_encoder = nyamagabe_label_encoders[nyamagabe_col]
        nyamagabe_data_row[nyamagabe_col] = nyamagabe_label_encoder.inverse_transform([nyamagabe_data_row[nyamagabe_col]])[0]
    return nyamagabe_data_row

# Function to perform prediction
def nyamagabe_predict_landslide(nyamagabe_data_row):
    # Encode categorical data
    nyamagabe_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for nyamagabe_col in nyamagabe_categorical_cols:
        nyamagabe_data_row[nyamagabe_col] = nyamagabe_label_encoders[nyamagabe_col].transform([nyamagabe_data_row[nyamagabe_col]])[0]
    
    # Remove the last two columns
    nyamagabe_data_row = nyamagabe_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    nyamagabe_probability = nyamagabe_model.predict_proba(nyamagabe_data_row.values.reshape(1, -1))[0]
    return nyamagabe_probability, nyamagabe_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def nyamagabe_predict_landslide_occurrence(nyamagabe_file_path):
    global nyamagabe_predicted_results
    while True:
        # Load CSV file
        nyamagabe_data = pd.read_csv(nyamagabe_file_path)
        nyamagabe_num_rows = len(nyamagabe_data)
        
        # Iterate through each row
        for nyamagabe_i in range(nyamagabe_num_rows):
            nyamagabe_row_data = nyamagabe_data.iloc[nyamagabe_i]
            nyamagabe_longitude = nyamagabe_row_data['Longitude']
            nyamagabe_latitude = nyamagabe_row_data['Latitude']
            nyamagabe_probability, nyamagabe_input_data = nyamagabe_predict_landslide(nyamagabe_row_data)
            
            nyamagabe_landslide_probability = nyamagabe_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            nyamagabe_input_data_decoded = nyamagabe_decode_categorical(nyamagabe_input_data)
            
            # Append the predicted results to the DataFrame
            nyamagabe_new_row = {'Longitude': nyamagabe_longitude,
                                 'Latitude': nyamagabe_latitude,
                                 **nyamagabe_input_data_decoded.to_dict(),
                                 'Landslide_Probability': nyamagabe_landslide_probability}
            nyamagabe_predicted_results = pd.concat([nyamagabe_predicted_results, pd.DataFrame([nyamagabe_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            nyamagabe_predicted_results.to_csv('nyamagabe/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('nyamagabe/predicted_results.csv') and os.path.getsize('nyamagabe/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('nyamagabe/archive'):
                    os.makedirs('nyamagabe/archive')
                # Append timestamp to the copied file name
                nyamagabe_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                nyamagabe_archive_file_name = f'nyamagabe/archive/predicted_results_copy_{nyamagabe_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('nyamagabe/predicted_results.csv', nyamagabe_archive_file_name)
                # Reinitialize the nyamagabe_predicted_results DataFrame
                nyamagabe_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *nyamagabe_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if nyamagabe_i == nyamagabe_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/nyamapredict')
def nyamagabe_predict():
    nyamagabe_file_path = 'nyamagabe/nyamagabe_inputs.csv'
    nyamagabe_predict_landslide_occurrence(nyamagabe_file_path)
    return redirect(url_for('Nyamagabe'))


# Load the trained model and label encoders
nyabihu_model = joblib.load('nyabihu/nyabihu.pkl')
nyabihu_label_encoders = joblib.load('nyabihu/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
nyabihu_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *nyabihu_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def nyabihu_decode_categorical(nyabihu_data_row):
    # Decode categorical data
    nyabihu_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for nyabihu_col in nyabihu_categorical_cols:
        nyabihu_label_encoder = nyabihu_label_encoders[nyabihu_col]
        nyabihu_data_row[nyabihu_col] = nyabihu_label_encoder.inverse_transform([nyabihu_data_row[nyabihu_col]])[0]
    return nyabihu_data_row

# Function to perform prediction
def nyabihu_predict_landslide(nyabihu_data_row):
    # Encode categorical data
    nyabihu_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for nyabihu_col in nyabihu_categorical_cols:
        nyabihu_data_row[nyabihu_col] = nyabihu_label_encoders[nyabihu_col].transform([nyabihu_data_row[nyabihu_col]])[0]
    
    # Remove the last two columns
    nyabihu_data_row = nyabihu_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    nyabihu_probability = nyabihu_model.predict_proba(nyabihu_data_row.values.reshape(1, -1))[0]
    return nyabihu_probability, nyabihu_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def nyabihu_predict_landslide_occurrence(nyabihu_file_path):
    global nyabihu_predicted_results
    while True:
        # Load CSV file
        nyabihu_data = pd.read_csv(nyabihu_file_path)
        nyabihu_num_rows = len(nyabihu_data)
        
        # Iterate through each row
        for nyabihu_i in range(nyabihu_num_rows):
            nyabihu_row_data = nyabihu_data.iloc[nyabihu_i]
            nyabihu_longitude = nyabihu_row_data['Longitude']
            nyabihu_latitude = nyabihu_row_data['Latitude']
            nyabihu_probability, nyabihu_input_data = nyabihu_predict_landslide(nyabihu_row_data)
            
            nyabihu_landslide_probability = nyabihu_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            nyabihu_input_data_decoded = nyabihu_decode_categorical(nyabihu_input_data)
            
            # Append the predicted results to the DataFrame
            nyabihu_new_row = {'Longitude': nyabihu_longitude,
                                 'Latitude': nyabihu_latitude,
                                 **nyabihu_input_data_decoded.to_dict(),
                                 'Landslide_Probability': nyabihu_landslide_probability}
            nyabihu_predicted_results = pd.concat([nyabihu_predicted_results, pd.DataFrame([nyabihu_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            nyabihu_predicted_results.to_csv('nyabihu/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('nyabihu/predicted_results.csv') and os.path.getsize('nyabihu/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('nyabihu/archive'):
                    os.makedirs('nyabihu/archive')
                # Append timestamp to the copied file name
                nyabihu_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                nyabihu_archive_file_name = f'nyabihu/archive/predicted_results_copy_{nyabihu_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('nyabihu/predicted_results.csv', nyabihu_archive_file_name)
                # Reinitialize the nyabihu_predicted_results DataFrame
                nyabihu_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *nyabihu_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if nyabihu_i == nyabihu_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/nyapredict')
def nyabihu_predict():
    nyabihu_file_path = 'nyabihu/nyabihu_inputs.csv'
    nyabihu_predict_landslide_occurrence(nyabihu_file_path)
    return redirect(url_for('Nyabihu'))


# Load the trained model and label encoders
musanze_model = joblib.load('musanze/musanze.pkl')
musanze_label_encoders = joblib.load('musanze/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
musanze_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *musanze_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def musanze_decode_categorical(musanze_data_row):
    # Decode categorical data
    musanze_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for musanze_col in musanze_categorical_cols:
        musanze_label_encoder = musanze_label_encoders[musanze_col]
        musanze_data_row[musanze_col] = musanze_label_encoder.inverse_transform([musanze_data_row[musanze_col]])[0]
    return musanze_data_row

# Function to perform prediction
def musanze_predict_landslide(musanze_data_row):
    # Encode categorical data
    musanze_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for musanze_col in musanze_categorical_cols:
        musanze_data_row[musanze_col] = musanze_label_encoders[musanze_col].transform([musanze_data_row[musanze_col]])[0]
    
    # Remove the last two columns
    musanze_data_row = musanze_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    musanze_probability = musanze_model.predict_proba(musanze_data_row.values.reshape(1, -1))[0]
    return musanze_probability, musanze_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def musanze_predict_landslide_occurrence(musanze_file_path):
    global musanze_predicted_results
    while True:
        # Load CSV file
        musanze_data = pd.read_csv(musanze_file_path)
        musanze_num_rows = len(musanze_data)
        
        # Iterate through each row
        for musanze_i in range(musanze_num_rows):
            musanze_row_data = musanze_data.iloc[musanze_i]
            musanze_longitude = musanze_row_data['Longitude']
            musanze_latitude = musanze_row_data['Latitude']
            musanze_probability, musanze_input_data = musanze_predict_landslide(musanze_row_data)
            
            musanze_landslide_probability = musanze_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            musanze_input_data_decoded = musanze_decode_categorical(musanze_input_data)
            
            # Append the predicted results to the DataFrame
            musanze_new_row = {'Longitude': musanze_longitude,
                                 'Latitude': musanze_latitude,
                                 **musanze_input_data_decoded.to_dict(),
                                 'Landslide_Probability': musanze_landslide_probability}
            musanze_predicted_results = pd.concat([musanze_predicted_results, pd.DataFrame([musanze_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            musanze_predicted_results.to_csv('musanze/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('musanze/predicted_results.csv') and os.path.getsize('musanze/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('musanze/archive'):
                    os.makedirs('musanze/archive')
                # Append timestamp to the copied file name
                musanze_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                musanze_archive_file_name = f'musanze/archive/predicted_results_copy_{musanze_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('musanze/predicted_results.csv', musanze_archive_file_name)
                # Reinitialize the musanze_predicted_results DataFrame
                musanze_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *musanze_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if musanze_i == musanze_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/mupredict')
def musanze_predict():
    musanze_file_path = 'musanze/musanze_inputs.csv'
    musanze_predict_landslide_occurrence(musanze_file_path)
    return redirect(url_for('Musanze'))


# Load the trained model and label encoders
karongi_model = joblib.load('karongi/karongi.pkl')
karongi_label_encoders = joblib.load('karongi/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
karongi_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *karongi_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def karongi_decode_categorical(karongi_data_row):
    # Decode categorical data
    karongi_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for karongi_col in karongi_categorical_cols:
        karongi_label_encoder = karongi_label_encoders[karongi_col]
        karongi_data_row[karongi_col] = karongi_label_encoder.inverse_transform([karongi_data_row[karongi_col]])[0]
    return karongi_data_row

# Function to perform prediction
def karongi_predict_landslide(karongi_data_row):
    # Encode categorical data
    karongi_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for karongi_col in karongi_categorical_cols:
        karongi_data_row[karongi_col] = karongi_label_encoders[karongi_col].transform([karongi_data_row[karongi_col]])[0]
    
    # Remove the last two columns
    karongi_data_row = karongi_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    karongi_probability = karongi_model.predict_proba(karongi_data_row.values.reshape(1, -1))[0]
    return karongi_probability, karongi_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def karongi_predict_landslide_occurrence(karongi_file_path):
    global karongi_predicted_results
    while True:
        # Load CSV file
        karongi_data = pd.read_csv(karongi_file_path)
        karongi_num_rows = len(karongi_data)
        
        # Iterate through each row
        for karongi_i in range(karongi_num_rows):
            karongi_row_data = karongi_data.iloc[karongi_i]
            karongi_longitude = karongi_row_data['Longitude']
            karongi_latitude = karongi_row_data['Latitude']
            karongi_probability, karongi_input_data = karongi_predict_landslide(karongi_row_data)
            
            karongi_landslide_probability = karongi_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            karongi_input_data_decoded = karongi_decode_categorical(karongi_input_data)
            
            # Append the predicted results to the DataFrame
            karongi_new_row = {'Longitude': karongi_longitude,
                                 'Latitude': karongi_latitude,
                                 **karongi_input_data_decoded.to_dict(),
                                 'Landslide_Probability': karongi_landslide_probability}
            karongi_predicted_results = pd.concat([karongi_predicted_results, pd.DataFrame([karongi_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            karongi_predicted_results.to_csv('karongi/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('karongi/predicted_results.csv') and os.path.getsize('karongi/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('karongi/archive'):
                    os.makedirs('karongi/archive')
                # Append timestamp to the copied file name
                karongi_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                karongi_archive_file_name = f'karongi/archive/predicted_results_copy_{karongi_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('karongi/predicted_results.csv', karongi_archive_file_name)
                # Reinitialize the karongi_predicted_results DataFrame
                karongi_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *karongi_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if karongi_i == karongi_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/kapredict')
def karongi_predict():
    karongi_file_path = 'karongi/karongi_inputs.csv'
    karongi_predict_landslide_occurrence(karongi_file_path)
    return redirect(url_for('Karongi'))


# Load the trained model and label encoders
gicumbi_model = joblib.load('gicumbi/gicumbi.pkl')
gicumbi_label_encoders = joblib.load('gicumbi/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
gicumbi_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *gicumbi_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def gicumbi_decode_categorical(gicumbi_data_row):
    # Decode categorical data
    gicumbi_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for gicumbi_col in gicumbi_categorical_cols:
        gicumbi_label_encoder = gicumbi_label_encoders[gicumbi_col]
        gicumbi_data_row[gicumbi_col] = gicumbi_label_encoder.inverse_transform([gicumbi_data_row[gicumbi_col]])[0]
    return gicumbi_data_row

# Function to perform prediction
def gicumbi_predict_landslide(gicumbi_data_row):
    # Encode categorical data
    gicumbi_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for gicumbi_col in gicumbi_categorical_cols:
        gicumbi_data_row[gicumbi_col] = gicumbi_label_encoders[gicumbi_col].transform([gicumbi_data_row[gicumbi_col]])[0]
    
    # Remove the last two columns
    gicumbi_data_row = gicumbi_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    gicumbi_probability = gicumbi_model.predict_proba(gicumbi_data_row.values.reshape(1, -1))[0]
    return gicumbi_probability, gicumbi_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def gicumbi_predict_landslide_occurrence(gicumbi_file_path):
    global gicumbi_predicted_results
    while True:
        # Load CSV file
        gicumbi_data = pd.read_csv(gicumbi_file_path)
        gicumbi_num_rows = len(gicumbi_data)
        
        # Iterate through each row
        for gicumbi_i in range(gicumbi_num_rows):
            gicumbi_row_data = gicumbi_data.iloc[gicumbi_i]
            gicumbi_longitude = gicumbi_row_data['Longitude']
            gicumbi_latitude = gicumbi_row_data['Latitude']
            gicumbi_probability, gicumbi_input_data = gicumbi_predict_landslide(gicumbi_row_data)
            
            gicumbi_landslide_probability = gicumbi_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            gicumbi_input_data_decoded = gicumbi_decode_categorical(gicumbi_input_data)
            
            # Append the predicted results to the DataFrame
            gicumbi_new_row = {'Longitude': gicumbi_longitude,
                                 'Latitude': gicumbi_latitude,
                                 **gicumbi_input_data_decoded.to_dict(),
                                 'Landslide_Probability': gicumbi_landslide_probability}
            gicumbi_predicted_results = pd.concat([gicumbi_predicted_results, pd.DataFrame([gicumbi_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            gicumbi_predicted_results.to_csv('gicumbi/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('gicumbi/predicted_results.csv') and os.path.getsize('gicumbi/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('gicumbi/archive'):
                    os.makedirs('gicumbi/archive')
                # Append timestamp to the copied file name
                gicumbi_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                gicumbi_archive_file_name = f'gicumbi/archive/predicted_results_copy_{gicumbi_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('gicumbi/predicted_results.csv', gicumbi_archive_file_name)
                # Reinitialize the gicumbi_predicted_results DataFrame
                gicumbi_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *gicumbi_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if gicumbi_i == gicumbi_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/gipredict')
def gicumbi_predict():
    gicumbi_file_path = 'gicumbi/gicumbi_inputs.csv'
    gicumbi_predict_landslide_occurrence(gicumbi_file_path)
    return redirect(url_for('Gicumbi'))


# Load the trained model and label encoders
gakenke_model = joblib.load('gakenke/gakenke.pkl')
gakenke_label_encoders = joblib.load('gakenke/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
gakenke_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *gakenke_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def gakenke_decode_categorical(gakenke_data_row):
    # Decode categorical data
    gakenke_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for gakenke_col in gakenke_categorical_cols:
        gakenke_label_encoder = gakenke_label_encoders[gakenke_col]
        gakenke_data_row[gakenke_col] = gakenke_label_encoder.inverse_transform([gakenke_data_row[gakenke_col]])[0]
    return gakenke_data_row

# Function to perform prediction
def gakenke_predict_landslide(gakenke_data_row):
    # Encode categorical data
    gakenke_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for gakenke_col in gakenke_categorical_cols:
        gakenke_data_row[gakenke_col] = gakenke_label_encoders[gakenke_col].transform([gakenke_data_row[gakenke_col]])[0]
    
    # Remove the last two columns
    gakenke_data_row = gakenke_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    gakenke_probability = gakenke_model.predict_proba(gakenke_data_row.values.reshape(1, -1))[0]
    return gakenke_probability, gakenke_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def gakenke_predict_landslide_occurrence(gakenke_file_path):
    global gakenke_predicted_results
    while True:
        # Load CSV file
        gakenke_data = pd.read_csv(gakenke_file_path)
        gakenke_num_rows = len(gakenke_data)
        
        # Iterate through each row
        for gakenke_i in range(gakenke_num_rows):
            gakenke_row_data = gakenke_data.iloc[gakenke_i]
            gakenke_longitude = gakenke_row_data['Longitude']
            gakenke_latitude = gakenke_row_data['Latitude']
            gakenke_probability, gakenke_input_data = gakenke_predict_landslide(gakenke_row_data)
            
            gakenke_landslide_probability = gakenke_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            gakenke_input_data_decoded = gakenke_decode_categorical(gakenke_input_data)
            
            # Append the predicted results to the DataFrame
            gakenke_new_row = {'Longitude': gakenke_longitude,
                                 'Latitude': gakenke_latitude,
                                 **gakenke_input_data_decoded.to_dict(),
                                 'Landslide_Probability': gakenke_landslide_probability}
            gakenke_predicted_results = pd.concat([gakenke_predicted_results, pd.DataFrame([gakenke_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            gakenke_predicted_results.to_csv('gakenke/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('gakenke/predicted_results.csv') and os.path.getsize('gakenke/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('gakenke/archive'):
                    os.makedirs('gakenke/archive')
                # Append timestamp to the copied file name
                gakenke_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                gakenke_archive_file_name = f'gakenke/archive/predicted_results_copy_{gakenke_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('gakenke/predicted_results.csv', gakenke_archive_file_name)
                # Reinitialize the gakenke_predicted_results DataFrame
                gakenke_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *gakenke_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if gakenke_i == gakenke_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/gapredict')
def gakenke_predict():
    gakenke_file_path = 'gakenke/gakenke_inputs.csv'
    gakenke_predict_landslide_occurrence(gakenke_file_path)
    return redirect(url_for('Gakenke'))

# Load the trained model and label encoders
Burera_model = joblib.load('Burera/burera.pkl')
Burera_label_encoders = joblib.load('Burera/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
Burera_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *Burera_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def Burera_decode_categorical(Burera_data_row):
    # Decode categorical data
    Burera_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for Burera_col in Burera_categorical_cols:
        Burera_label_encoder = Burera_label_encoders[Burera_col]
        Burera_data_row[Burera_col] = Burera_label_encoder.inverse_transform([Burera_data_row[Burera_col]])[0]
    return Burera_data_row

# Function to perform prediction
def Burera_predict_landslide(Burera_data_row):
    # Encode categorical data
    Burera_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for Burera_col in Burera_categorical_cols:
        Burera_data_row[Burera_col] = Burera_label_encoders[Burera_col].transform([Burera_data_row[Burera_col]])[0]
    
    # Remove the last two columns
    Burera_data_row = Burera_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    Burera_probability = Burera_model.predict_proba(Burera_data_row.values.reshape(1, -1))[0]
    return Burera_probability, Burera_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def Burera_predict_landslide_occurrence(Burera_file_path):
    global Burera_predicted_results
    while True:
        # Load CSV file
        Burera_data = pd.read_csv(Burera_file_path)
        Burera_num_rows = len(Burera_data)
        
        # Iterate through each row
        for Burera_i in range(Burera_num_rows):
            Burera_row_data = Burera_data.iloc[Burera_i]
            Burera_longitude = Burera_row_data['Longitude']
            Burera_latitude = Burera_row_data['Latitude']
            Burera_probability, Burera_input_data = Burera_predict_landslide(Burera_row_data)
            
            Burera_landslide_probability = Burera_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            Burera_input_data_decoded = Burera_decode_categorical(Burera_input_data)
            
            # Append the predicted results to the DataFrame
            Burera_new_row = {'Longitude': Burera_longitude,
                                 'Latitude': Burera_latitude,
                                 **Burera_input_data_decoded.to_dict(),
                                 'Landslide_Probability': Burera_landslide_probability}
            Burera_predicted_results = pd.concat([Burera_predicted_results, pd.DataFrame([Burera_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            Burera_predicted_results.to_csv('Burera/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('Burera/predicted_results.csv') and os.path.getsize('Burera/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('Burera/archive'):
                    os.makedirs('Burera/archive')
                # Append timestamp to the copied file name
                Burera_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                Burera_archive_file_name = f'Burera/archive/predicted_results_copy_{Burera_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('Burera/predicted_results.csv', Burera_archive_file_name)
                # Reinitialize the Burera_predicted_results DataFrame
                Burera_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *Burera_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if Burera_i == Burera_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/bupredict')
def Burera_predict():
    Burera_file_path = 'Burera/Burera_inputs.csv'
    Burera_predict_landslide_occurrence(Burera_file_path)
    return redirect(url_for('Burera'))



# Load the trained model and label encoders
ngororero_model = joblib.load('ngororero/ngororero.pkl')
ngororero_label_encoders = joblib.load('ngororero/label_encoders.pkl')

# Initialize an empty DataFrame to store the predicted results
ngororero_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *ngororero_label_encoders.keys(), 'Landslide_Probability'])

# Function to decode categorical data
def ngororero_decode_categorical(ngororero_data_row):
    # Decode categorical data
    ngororero_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for ngororero_col in ngororero_categorical_cols:
        ngororero_label_encoder = ngororero_label_encoders[ngororero_col]
        ngororero_data_row[ngororero_col] = ngororero_label_encoder.inverse_transform([ngororero_data_row[ngororero_col]])[0]
    return ngororero_data_row

# Function to perform prediction
def ngororero_predict_landslide(ngororero_data_row):
    # Encode categorical data
    ngororero_categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
    for ngororero_col in ngororero_categorical_cols:
        ngororero_data_row[ngororero_col] = ngororero_label_encoders[ngororero_col].transform([ngororero_data_row[ngororero_col]])[0]
    
    # Remove the last two columns
    ngororero_data_row = ngororero_data_row.iloc[:-2].copy()  # Make a copy to avoid SettingWithCopyWarning
    
    # Make prediction
    ngororero_probability = ngororero_model.predict_proba(ngororero_data_row.values.reshape(1, -1))[0]
    return ngororero_probability, ngororero_data_row

# Function to iterate through the CSV file rows and predict landslide occurrence
def ngororero_predict_landslide_occurrence(ngororero_file_path):
    global ngororero_predicted_results
    while True:
        # Load CSV file
        ngororero_data = pd.read_csv(ngororero_file_path)
        ngororero_num_rows = len(ngororero_data)
        
        # Iterate through each row
        for ngororero_i in range(ngororero_num_rows):
            ngororero_row_data = ngororero_data.iloc[ngororero_i]
            ngororero_longitude = ngororero_row_data['Longitude']
            ngororero_latitude = ngororero_row_data['Latitude']
            ngororero_probability, ngororero_input_data = ngororero_predict_landslide(ngororero_row_data)
            
            ngororero_landslide_probability = ngororero_probability[1] * 100  # Probability of landslide
            
            # print(f"At coordinates (Longitude: {longitude}, Latitude: {latitude}), input data: {input_data}, landslide probability: {landslide_probability:.2f}%")
            
            # Decode categorical data before exporting input data
            ngororero_input_data_decoded = ngororero_decode_categorical(ngororero_input_data)
            
            # Append the predicted results to the DataFrame
            ngororero_new_row = {'Longitude': ngororero_longitude,
                                 'Latitude': ngororero_latitude,
                                 **ngororero_input_data_decoded.to_dict(),
                                 'Landslide_Probability': ngororero_landslide_probability}
            ngororero_predicted_results = pd.concat([ngororero_predicted_results, pd.DataFrame([ngororero_new_row])], ignore_index=True)
            
            # Export the DataFrame to a CSV file
            ngororero_predicted_results.to_csv('ngororero/predicted_results.csv', index=False)
            
            # Check if the CSV file size exceeds 50 KB
            if os.path.exists('ngororero/predicted_results.csv') and os.path.getsize('ngororero/predicted_results.csv') > 50 * 1024:
                # Create an archive folder if it doesn't exist
                if not os.path.exists('ngororero/archive'):
                    os.makedirs('ngororero/archive')
                # Append timestamp to the copied file name
                ngororero_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                ngororero_archive_file_name = f'ngororero/archive/predicted_results_copy_{ngororero_timestamp}.csv'
                # Copy the CSV file to the archive folder with timestamped name
                shutil.copy('ngororero/predicted_results.csv', ngororero_archive_file_name)
                # Reinitialize the ngororero_predicted_results DataFrame
                ngororero_predicted_results = pd.DataFrame(columns=['Longitude', 'Latitude', *ngororero_label_encoders.keys(), 'Landslide_Probability'])
            
            # Delay before reading the next row (adjust as needed)
            time.sleep(1)  # 1 second delay
            
            # If it's the last row, start from the beginning
            if ngororero_i == ngororero_num_rows - 1:
                # print("Reached the last row. Starting from the beginning.")
                break

@app.route('/ngpredict')
def ngororero_predict():
    ngororero_file_path = 'ngororero/ngororero_inputs.csv'
    ngororero_predict_landslide_occurrence(ngororero_file_path)
    return redirect(url_for('Ngororero'))


# Fixed username and password
fixed_username = 'geohome@info.com'
fixed_password = 'geohome'



# Define routes for each district
@app.route('/Burera')
def burera():
    try:
        # Check if the CSV file exists
        if not os.path.exists('burera/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('burera/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Burera.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Gakenke')
def gakenke():
    try:
        # Check if the CSV file exists
        if not os.path.exists('gakenke/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('gakenke/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Gakenke.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Gicumbi')
def gicumbi():
    try:
        # Check if the CSV file exists
        if not os.path.exists('gicumbi/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('gicumbi/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Gicumbi.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Musanze')
def musanze():
    try:
        # Check if the CSV file exists
        if not os.path.exists('musanze/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('musanze/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Musanze.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Rulindo')
def rulindo():
    try:
        # Check if the CSV file exists
        if not os.path.exists('rulindo/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('rulindo/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Rulindo.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Karongi')
def karongi():
    try:
        # Check if the CSV file exists
        if not os.path.exists('karongi/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('karongi/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Karongi.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Nyabihu')
def nyabihu():
    try:
        # Check if the CSV file exists
        if not os.path.exists('nyabihu/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('nyabihu/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Nyabihu.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Rubavu')
def rubavu():
    try:
        # Check if the CSV file exists
        if not os.path.exists('rubavu/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('rubavu/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Rubavu.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Rusizi')
def rusizi():
    try:
        # Check if the CSV file exists
        if not os.path.exists('rusizi/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('rusizi/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Rusizi.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Ngororero')
def ngororero():
    try:
        # Check if the CSV file exists
        if not os.path.exists('ngororero/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('ngororero/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Ngororero.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Nyamasheke')
def nyamasheke():
    try:
        # Check if the CSV file exists
        if not os.path.exists('nyamasheke/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('nyamasheke/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Nyamasheke.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Rutsiro')
def rutsiro():
    try:
        # Check if the CSV file exists
        if not os.path.exists('rutsiro/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('rutsiro/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Rutsiro.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Nyamagabe')
def nyamagabe():
    try:
        # Check if the CSV file exists
        if not os.path.exists('nyamagabe/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('nyamagabe/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Nyamagabe.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/', methods=['GET'])  # Specify the allowed HTTP method
def index():
    try:
        # Check if the CSV file exists
        if not os.path.exists('ngororero/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('ngororero/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Burera.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            if username == fixed_username and password == fixed_password:
                # Read the last record from the CSV file
                with open('Burera/predicted_results.csv', newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    data = list(reader)

                # Check if data is empty
                if not data:
                    time.sleep(2)  # Sleep for 2 seconds before retrying
                    flash('No data available.', 'danger')
                    return redirect(url_for('login'))  # Redirect to login page

                # Get the last record
                last_record = data[-1]

                # Format numeric values to have only 5 digits after the decimal point
                formatted_record = {}
                for key, value in last_record.items():
                    if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                        formatted_record[key] = "{:.5f}".format(float(value))
                    else:
                        formatted_record[key] = value

                return render_template('Burera.html', record=formatted_record)
            else:
                flash('Login failed. Please check your username and password.', 'danger')

        return render_template('login.html')
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        flash('An error occurred. Please try again later.', 'danger')
        return redirect(url_for('login'))  # Redirect to login page


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/setting')
def setting():
    # Add setting functionality here
    return render_template('setting.html')

@app.route('/warnings')
def warnings():
    # Add setting functionality here
    return render_template('warnings.html')

@app.route('/contact')
def contact():
    # Add contact functionality here
    return render_template('contact.html')

@app.route('/about')
def about():
    # Add about functionality here
    return render_template('about.html')

@app.route('/Ngororeroexports')
def ngororeroexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'ngororero/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('ngororeroexports.html', csv_files=csv_files)

@app.route('/ngororerodownload/<filename>')
def ngororerodownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'ngororero/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Bureraexports')
def bureraexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'Burera/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Bureraexports.html', csv_files=csv_files)

@app.route('/bureradownload/<filename>')
def bureradownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'Burera/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Gakenkeexports')
def gakenkeexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'gakenke/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Gakenkeexports.html', csv_files=csv_files)

@app.route('/gakenkedownload/<filename>')
def gakenkedownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'gakenke/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Gicumbiexports')
def gicumbiexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'gicumbi/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Gicumbiexports.html', csv_files=csv_files)

@app.route('/gicumbidownload/<filename>')
def gicumbidownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'gicumbi/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Karongiexports')
def karongiexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'karongi/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Karongiexports.html', csv_files=csv_files)

@app.route('/karongidownload/<filename>')
def karongidownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'karongi/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Musanzeexports')
def musanzeexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'musanze/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Musanzeexports.html', csv_files=csv_files)

@app.route('/musanzedownload/<filename>')
def musanzedownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'musanze/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Nyabihuexports')
def nyabihuexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'nyabihu/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Nyabihuexports.html', csv_files=csv_files)

@app.route('/nyabihudownload/<filename>')
def nyabihudownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'nyabihu/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Nyamagabeexports')
def nyamagabeexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'nyamagabe/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Nyamagabeexports.html', csv_files=csv_files)

@app.route('/nyamagabedownload/<filename>')
def nyamagabedownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'nyamagabe/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Nyamashekeexports')
def nyamashekeexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'nyamasheke/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Nyamashekeexports.html', csv_files=csv_files)

@app.route('/nyamashekedownload/<filename>')
def nyamashekedownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'nyamasheke/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Rubavuexports')
def rubavuexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'rubavu/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Rubavuexports.html', csv_files=csv_files)

@app.route('/rubavudownload/<filename>')
def rubavudownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'rubavu/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Rulindoexports')
def rulindoexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'rulindo/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Rulindoexports.html', csv_files=csv_files)

@app.route('/rulindodownload/<filename>')
def rulindodownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'rulindo/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Rusiziexports')
def rusiziexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'rusizi/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Rusiziexports.html', csv_files=csv_files)

@app.route('/rusizidownload/<filename>')
def rusizidownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'rusizi/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)

@app.route('/Rutsiroexports')
def rutsiroexports():
    

    # Define the directory path where CSV files are stored
    archive_folder = 'rutsiro/archive'

    # Get the list of CSV files in the archive folder
    csv_files = [f for f in os.listdir(archive_folder) if f.endswith('.csv')]

    # Render the template with the list of CSV files
    return render_template('Rutsiroexports.html', csv_files=csv_files)

@app.route('/rutsirodownload/<filename>')
def rutsirodownload_file(filename):
    # Define the directory path where CSV files are stored
    archive_folder = 'rutsiro/archive'

    # Return the CSV file for download
    return send_from_directory(archive_folder, filename, as_attachment=True)


@app.route('/Bureralive')
def bureralive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('burera/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('burera/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Bureralive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Gakenkelive')
def gakenkelive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('gakenke/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('gakenke/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Gakenkelive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Gicumbilive')
def gicumbilive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('gicumbi/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('gicumbi/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Gicumbilive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Musanzelive')
def musanzelive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('musanze/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('musanze/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Musanzelive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Rulindolive')
def rulindolive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('rulindo/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('rulindo/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Rulindolive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Karongilive')
def karongilive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('karongi/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('karongi/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Karongilive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Nyabihulive')
def nyabihulive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('nyabihu/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('nyabihu/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Nyabihulive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Rubavulive')
def rubavulive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('rubavu/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('rubavu/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Rubavulive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Rusizilive')
def rusizilive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('rusizi/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('rusizi/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Rusizilive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Ngororerolive')
def ngororerolive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('ngororero/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('ngororero/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Ngororerolive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Nyamashekelive')
def nyamashekelive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('nyamasheke/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('nyamasheke/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Nyamashekelive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Rutsirolive')
def rutsirolive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('rutsiro/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('rutsiro/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Rutsirolive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."

@app.route('/Nyamagabelive')
def nyamagabelive():
    try:
        # Check if the CSV file exists
        if not os.path.exists('nyamagabe/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('nyamagabe/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('Nyamagabelive.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."


@app.route('/livedata', methods=['GET'])  # Specify the allowed HTTP method
def livedata():
    try:
        # Check if the CSV file exists
        if not os.path.exists('ngororero/predicted_results.csv'):
            return "CSV file not found."

        # Read the CSV file
        with open('ngororero/predicted_results.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            data = list(reader)

        # Check if data is empty
        if not data:
            time.sleep(2)  # Sleep for 2 seconds before retrying
            return "No data available."

        # Get the last record
        last_record = data[-1]

        # Format numeric values to have only 5 digits after the decimal point
        formatted_record = {}
        for key, value in last_record.items():
            if isinstance(value, str) and value.replace('.', '', 1).isdigit():
                formatted_record[key] = "{:.5f}".format(float(value))
            else:
                formatted_record[key] = value

        # Render the template with the formatted last record data
        return render_template('livedata.html', record=formatted_record)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        traceback.print_exc()  # Print traceback for debugging
        return "An error occurred. Please try again later."
    




if __name__ == '__main__':
    app.run(debug=True)
