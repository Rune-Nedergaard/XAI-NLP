import requests
import pandas as pd
from tqdm import tqdm
import concurrent.futures

'''
This script does the following:
1) Takes the 'answer_id' from the answers csv file and uses it to scrape the links from ODA
2) It then adds the links to the answers csv file and saves it to a new csv file
'''

def get_filurls(answer_id, retries=3):
    filurls = []
    for i in range(retries):
        try:
            r = requests.get(documents_baseurl + '(' + str(answer_id) + ')')
            documents = r.json()['value']
            for document in documents:
                if 'filurl' in document:
                    filurls.append(document['filurl'])
            if filurls:
                return filurls
        except:
            if i == retries - 1:
                return None

if __name__ == '__main__':
    questions = pd.read_csv('data/raw/questions_with_answers.csv')
    answer_ids = questions['answer_id'].tolist()
    documents_baseurl = 'https://oda.ft.dk/api/Dokument'
    filurls = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_filurls, answer_id) for answer_id in answer_ids]
        for future in tqdm(futures):
            try:
                filurl = future.result()
                if filurl:
                    filurls.append(filurl)
            except Exception as exc:
                print(f'Answer_id {answer_id} generated an exception: {exc}')
    questions['filurl'] = filurls
    questions.to_csv('data/raw/questions_with_filurls.csv', index=False)
