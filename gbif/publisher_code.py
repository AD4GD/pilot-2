import pandas as pd
import requests
from bs4 import BeautifulSoup

# read the CSV file into a pandas DataFrame
df = pd.read_csv('c:\Users\kriukovv\Documents\gbif\input\0014969-240202131308920.csv')

# get unique values from the "publishingOrgKey" column
publisher = df['publishingOrgKey'].unique()

# create a new column to store the headers
df['website_header'] = ''

# loop through unique keys, retrieve header, and update the DataFrame
for key in publisher:
    # assuming URLs are stored in a column named 'URL' in the DataFrame
    url = df[df['publishingOrgKey'] == key]['URL'].iloc[0]
    
    # make an HTTP request to get the headers
    response = requests.get(url)
    
    # check if the request was successful
    if response.status_code == 200:
        # get the headers
        headers = response.headers
        # store the desired header value in dataframe
        df.loc[df['publishingOrgKey'] == key, 'website_header'] = headers['YourDesiredHeader']

# save the updated DataFrame to a new CSV file
df.to_csv('csv_publisher.csv', index=False)


