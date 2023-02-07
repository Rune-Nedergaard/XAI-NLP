import requests
import pandas as pd
from tqdm import tqdm
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

def get_answer_to_question(url):
    '''
    This function takes the url and scrapes all the answers from ODA
    '''
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



if __name__ == '__main__':
    print("Scraping answers from ODA")

    tqdm.pandas()
    #we want to scrape the answers id to all the questions and add them to the questions csv file as a new column
    questions['answers_id'] = questions['id'].progress_apply(lambda x: get_answer_to_question(base_url + str(x)))
    #save the questions csv file with the answers id as a new csv file called answers
    questions.to_csv('data/raw/answers.csv', index=False)