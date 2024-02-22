import pandas as pd
import os

# Specify the path to your CSV file
parent_dir = os.getcwd()
#csv_file_path = os.path.join(parent_dir,'issue_count.csv')
csv_file_path = r'C:\Users\kriukovv\Documents\gbif\output\issue_count.csv'

# Read the CSV file into a DataFrame
df = pd.read_csv(csv_file_path)

# Assuming 'source' is the name of the column containing the values
stacked_values = df['issue'].str.split(';', expand=True).stack()

# Extract unique values
unique_values = stacked_values.unique()

print(unique_values)

result_df = pd.DataFrame({'issue': unique_values, 'importance': ''})

# Save the dataframe to a CSV file
result_df.to_csv(r'C:\Users\kriukovv\Documents\gbif\output\issue_types.csv', index=False)