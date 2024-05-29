import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
import numpy as np

# Get the current working directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# CSV file path
csv_file = os.path.join(current_dir, 'data/m2_survey_data.csv')

# Function to clean column names
def clean_column_name(col):
    return col.strip().replace(' ', '_').replace('-', '_').replace('/', '_').replace('(', '').replace(')', '').replace("'", "")

# Function to handle NaN values
def handle_nan(value):
    if pd.isna(value):
        return None
    return value

# Connect to the MySQL database
try:
    connection = mysql.connector.connect(
        host='localhost',
        database='stackoverflow_survey_db',
        user='root',
        password=''
    )

    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()

        # Read the CSV file
        df = pd.read_csv(csv_file)

        # Clean column names
        df.columns = [clean_column_name(col) for col in df.columns]

        # Prepare columns list and data types for MySQL
        columns = df.columns

        # Create the MySQL table
        table_name = 'survey_results_2019'
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        create_table_query = f"CREATE TABLE {table_name} (\
            id INT AUTO_INCREMENT PRIMARY KEY,\
            {', '.join([f'{col} TEXT' for col in columns if col != 'Respondent'])})"

        cursor.execute(create_table_query)
        print(f"Table '{table_name}' successfully created.")

        # Insert DataFrame records into MySQL
        for i, row in df.iterrows():
            row = [handle_nan(val) for val in row]
            sql = f"INSERT INTO {table_name} ({', '.join(columns[1:])}) VALUES ({', '.join(['%s'] * (len(columns) - 1))})"
            cursor.execute(sql, tuple(row[1:]))

        connection.commit()
        print(f"{cursor.rowcount} records inserted.")

except Error as e:
    print("Error while connecting to MySQL", e)
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed.")
