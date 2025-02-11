import pandas as pd

# Read the CSV file
df = pd.read_csv('rcs/cities_list.csv')
print(df)
# Assume the column you want to convert to a list is named 'your_column'
your_column_list = df['City, Country'].tolist()

print(your_column_list)
