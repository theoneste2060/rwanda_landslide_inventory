import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from imblearn.over_sampling import SMOTE
import joblib

# Load the synthetic dataset
data = pd.read_csv('extended_synthetic_landslide_data.csv')

# Split data into features and target variable
X = data.drop(columns=['Landslide Occurrence (1 for Yes, 0 for No)'])
y = data['Landslide Occurrence (1 for Yes, 0 for No)']

# Encode categorical variables
categorical_cols = ['Soil Type', 'Orientation', 'Soil Texture', 'Geological Composition', 'Slope Aspect', 'Landform Type', 'Precipitation Type']
label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    X[col] = le.fit_transform(X[col])
    label_encoders[col] = le

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Apply SMOTE to balance the classes
smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)

# Initialize Gradient Boosting Classifier
model = GradientBoostingClassifier()

# Train the model on the resampled data with adjusted sample weights
sample_weights = [1 if class_ == 0 else 2 for class_ in y_train_resampled]
model.fit(X_train_resampled, y_train_resampled, sample_weight=sample_weights)

# Predictions on the test set
y_pred = model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)
class_report = classification_report(y_test, y_pred)

# Print evaluation metrics
print("Accuracy:", accuracy)
print("Confusion Matrix:\n", conf_matrix)
print("Classification Report:\n", class_report)

# Save the trained model and label encoders
joblib.dump(model, 'model.pkl')
joblib.dump(label_encoders, 'label_encoders.pkl')

print("Model and label encoders saved successfully.")
