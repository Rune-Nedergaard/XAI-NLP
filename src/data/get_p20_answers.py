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

            #check if there are multiple answers to a question
            if len(answers) > 1:
                #if there are multiple answers, we want the final answer
                #final answers have kategoriid = 22
                final_answer = [answer for answer in answers['value'] if answer['kategoriid'] == 22]
                final_answer = final_answer[0]['id']
                return final_answer
            
            elif len(answers) == 1:
                #if there is only one answer, we want that one
                return answers['value'][0]['id']
            
            else:
                #if there are no answers, we want to return None
                return None

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


    # print("Getting links from ODA")
    # links_baseurl = 'https://oda.ft.dk/api/Dokument'

    # answer_ids = questions['answer_id'].tolist()

    # filurls = []
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     futures = [executor.submit(get_filurls, answer_id) for answer_id in answer_ids]
    #     for future in tqdm(futures):
    #         try:
    #             filurl = future.result()
    #             if filurl:
    #                 filurls.append(filurl)
    #         except Exception as exc:
    #             print(f'Answer_id {answer_id} generated an exception: {exc}')
    # questions['filurl'] = filurls
    # questions.to_csv('data/raw/questions_with_filurls.csv', index=False)

    
    # #Trying to download pdfs
    # import ssl
    # import wget
    # ssl._create_default_https_context = ssl._create_unverified_context
    # bad_links = []

    # def download_pdf(url, filename):
    #     try: 
    #         wget.download(url, filename)
    #     except:
    #         print(f'Could not download {filename}')
    #         bad_links.append(filename)
    # links = questions['filurl'].tolist()
    # filenames = questions['answer_id'].tolist()


    # for link, filename in tqdm(zip(links, filenames)):
    #     if link:
    #         path = 'data/interim/' + str(filename) + '.pdf'
    #         download_pdf(link, filename)
    