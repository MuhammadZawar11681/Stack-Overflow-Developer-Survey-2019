# import os

# os.system('kaggle datasets download -d sagarvarandekar/stack-overflow-developer-survey-2019 -p ./data')
# os.system('unzip ./data/stack-overflow-developer-survey-2019.zip -d ./data')
import zipfile

with zipfile.ZipFile('data/stack-overflow-developer-survey-2019.zip', 'r') as zip_ref:
    zip_ref.extractall('data')  # Extract to a specific directory, e.g., 'data'
