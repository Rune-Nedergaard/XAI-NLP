import os
import time
from tqdm import tqdm
from google.cloud import translate_v2 as translate
translate_client = translate.Client()

def translate_text(text, target_language='en'):
    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

processed_folder = 'data/processed/'
translated_folder = 'data/translated/'

# Check if the translated folder exists, if not create it
if not os.path.exists(translated_folder):
    os.makedirs(translated_folder)

# Iterate through all files in the processed folder
for filename in tqdm(os.listdir(processed_folder)):
    # Check if the translated file already exists, if so, skip it
    translated_file_path = os.path.join(translated_folder, filename)
    if os.path.exists(translated_file_path):
        continue

    file_path = os.path.join(processed_folder, filename)
    # Skip file if its size is greater than 50kb
    if os.path.getsize(file_path) > 50 * 1024:
        continue

    with open(file_path, 'r', encoding='utf-8') as f:
        input_text = f.read()
    retries = 0
    while retries < 3:
        try:
            translated_text = translate_text(input_text)
            break
        except Exception as e:
            retries += 1
            if retries == 3:
                raise e
            time.sleep(1)

    with open(translated_file_path, 'w', encoding='utf-8') as f:
        f.write(translated_text)
