import requests
import json

URL = 'https://api.ohsome.org/v1/elements/geometry'
data = {"bboxes": "2.1358,41.3784,2.1758,41.4212", "properties": {"highway,width,bicycle"}, "time": "2017-06-01", "filter": "highway=tertiary"}
response = requests.post(URL, data=data)
print(response.json())

# check if the request was successful
if response.status_code == 200:
    geojson_data = response.json()  # parse the JSON response

    # save the GeoJSON data to a file
    with open('output.geojson', 'w') as geojson_file:
        json.dump(geojson_data, geojson_file)
    
    print("GeoJSON data saved to 'output.geojson'")
else:
    print(f"Request failed with status code {response.status_code}")



https://api.ohsome.org/v1/elements/geometry?bboxes=2.1358,41.3784,2.1758,41.4212&properties=tags&time=2012-06-01&filter=highway=tertiary

https://api.ohsome.org/v1/elements/geometry?bboxes=2.1358%2C41.3784%2C2.1758%2C41.4212&properties=highway%2Cwidth%2Cbicycle&time=2017-06-01&filter=highway%3Dtertiary






