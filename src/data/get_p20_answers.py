import requests
import pandas as pd
from tqdm import tqdm
import concurrent.futures
questions = pd.read_csv('data/raw/questions.csv')

'''
This script does the following:
1) Takes the 'id' from the questions csv file and uses it to scrape the answers from ODA
- The 'id' refers to the dokument-spørgsmålsid in the ODA API
2) Extracts the relevant information and saves the answers to a csv file
'''

# 1) Scraping answers from ODA
#This is the base url. The 'id' from the questions csv file is added to the end of the url
base_url = 'https://oda.ft.dk/api/Dokument?$inlinecount=allpages&$filter=sp%C3%B8rgsm%C3%A5lsid%20eq%20'

def batch_get_answers(url, retries=3):
    '''
    This function takes the url and scrapes all the answers from ODA
    '''
    for i in range(retries):
        try:
            r = requests.get(url)
            answers = r.json()
            prev = r.json()
            page = 1

            while 'odata.nextLink' in prev:

                r = requests.get(prev['odata.nextLink'])
                answers['value'] += r.json()['value']
                page += 1
                prev = r.json()

            #check if there are multiple answers to a question
            if len(answers['value']) > 1:
                #if there are multiple answers, we want the final answer
                #final answers have kategoriid = 22
                final_answer = [answer for answer in answers['value'] if answer['kategoriid'] == 22]
                return final_answer

            return answers
        except:
            if i == retries - 1:
                return None


'''
This script does the following:
1) Takes the 'answer_id' from the answers csv file and uses it to scrape the links from ODA
2) It then adds the links to the answers csv file and saves it to a new csv file
'''

def get_filurls(answer_id, retries=3):
    filurls = []
    for i in range(retries):
        try:
            r = requests.get(links_baseurl + '(' + str(answer_id) + ')')
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
    print("Getting answers from ODA")
    questions_ids = questions['id'].tolist()
    answers_id = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(batch_get_answers, base_url + str(question)) for question in questions_ids]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            try:
                answers_id.append(future.result())
            except Exception as exc:
                print(f'Question {question} generated an exception: {exc}')
    # 2) Extracting relevant information and saving them to a csv file
    #we just save the answer_ids to the questions csv file and save it to a new csv file
    questions['answer_id'] = answers_id
    questions.to_csv('data/raw/questions_with_answers.csv', index=False)


    print("Getting links from ODA")
    links_baseurl = 'https://oda.ft.dk/api/Dokument'

    answer_ids = questions['answer_id'].tolist()

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
