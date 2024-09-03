# to extract countries within the bounding box
import requests
import json

# ohsome API endpoint to extract full geometry
url = 'https://api.ohsome.org/v1/elements/geometry'
bbox = -2.7876213063263044,52.98893670759685,1.1889035388429525,54.755166952963556
data = {"bboxes": {bbox}, "filter": "boundary=administrative and admin_level=2", "properties": 'tags'}
response = requests.post(url, data=data)
print(response.json())

# check if the request was successful
if response.status_code == 200:
    response_json = response.json()
    
    # extract unique country names, filtering out None values
    # create set to handle only unique names
    unique_country_names = {
        feature['properties'].get('ISO3166-1:alpha3') 
        for feature in response_json.get('features', []) # filter out none values
        if feature['properties'].get('ISO3166-1:alpha3')
    }
    
    # print unique country names
    print("\n".join(unique_country_names))

    # save JSON response to GeoJSON
    with open('countries.geojson', 'w') as f:
        json.dump(response_json, f, indent=4)
else:
    print(f"Error: {response.status_code}")

