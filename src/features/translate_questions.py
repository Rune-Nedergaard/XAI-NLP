import os
import time
import pandas as pd
from tqdm import tqdm
from google.cloud import translate_v2 as translate
translate_client = translate.Client()

def translate_text(text, target_language='en'):
    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

df = pd.read_csv("data/raw/questions_with_answers.csv")
translated_folder = 'data/translated_questions/'

# Check if the translated folder exists, if not create it
if not os.path.exists(translated_folder):
    os.makedirs(translated_folder)

for index, row in tqdm(df.iterrows(), total=df.shape[0]):
    if pd.isna(row['titel']):
        continue
    input_text = row['titel']
    filename = f"question_{index}.txt"
    translated_file_path = os.path.join(translated_folder, filename)
    retries = 0
    while retries < 3:
        try:
            translated_text = translate_text(input_text)
            break
        except Exception as e:
            retries += 1
            if retries == 3:
                print(f"Failed to translate question {index} with title {input_text}")
                pass
            #time.sleep(1)

    with open(translated_file_path, 'w', encoding='utf-8') as f:
        f.write(translated_text)
        
    df.at[index, 'translated_questions'] = translated_text

df.to_csv("data/translated_questions.csv", index=False)
