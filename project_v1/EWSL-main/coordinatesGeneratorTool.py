from shapely.geometry import Point, Polygon
import numpy as np
import csv

# Define the polygon coordinates for Ngororero district in Rwanda
polygon_coords = [
    (-1.706534, 29.425907),
    (-2.037197, 29.572836),
    (-2.109115, 29.364937),
    (-1.758485, 29.228003)
]

# Create a Shapely polygon object
polygon = Polygon(polygon_coords)

# Function to generate latitude and longitude coordinates within the polygon
def generate_coordinates(polygon):
    min_x, min_y, max_x, max_y = polygon.bounds
    latitudes = np.arange(min_y, max_y, 0.01)
    longitudes = np.arange(min_x, max_x, 0.01)
    
    coordinates = []
    for lon in longitudes:
        for lat in latitudes:
            point = Point(lon, lat)
            if polygon.contains(point):
                coordinates.append((lat, lon))
    
    return coordinates

# Generate coordinates within the polygon
coordinates = generate_coordinates(polygon)

# Write coordinates to CSV file
csv_file_path = "rutsiro_coordinates.csv"
with open(csv_file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Latitude', 'Longitude'])
    writer.writerows(coordinates)

print(f"CSV file '{csv_file_path}' created successfully.")
