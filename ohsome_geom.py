import requests
import json

URL = 'https://api.ohsome.org/v1/elements/geometry'
data = {"bboxes": "8.625,49.3711,8.7334,49.4397", "properties": "tags", "time": "2023-06-01", "filter": "highway=tertiary"}
response = requests.post(URL, data=data)
print(response.json())

# Check if the request was successful
if response.status_code == 200:
    geojson_data = response.json()  # Parse the JSON response

    # Save the GeoJSON data to a file
    with open('output.geojson', 'w') as geojson_file:
        json.dump(geojson_data, geojson_file)
    
    print("GeoJSON data saved to 'output.geojson'")
else:
    print(f"Request failed with status code {response.status_code}")