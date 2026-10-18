
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