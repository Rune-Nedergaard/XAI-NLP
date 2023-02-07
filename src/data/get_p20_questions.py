import requests
import pandas as pd


''' 
This script does the following:
1) Scrapes all the §20 questions from ODA 
2) Extracts the relevant information and saves them to a csv file
'''

# 1) Scraping §20 questions from ODA
questions_url = 'https://oda.ft.dk/api/Dokument?$inlinecount=allpages&$filter=typeid%20eq%2016'
def get_all_questions(url):

    r = requests.get(url)

    questions = r.json()
    prev = r.json()
    page = 1

    while 'odata.nextLink' in prev:

        r = requests.get(prev['odata.nextLink'])
        questions['value'] += r.json()['value']
        if page % 50 == 0:
            print(f'Page {page} done')
        page += 1
        prev = r.json()

    return questions


# 2) Extracting relevant information and saving them to a csv file
def save_questions_to_csv(questions_json, datafolder='data/raw/', filename = 'questions.csv'):
    '''
    Saving json to a csv file
    '''

    questions = pd.DataFrame(questions_json['value'])
    questions.to_csv(datafolder + filename, index=False)



if __name__ == '__main__':
    questions_json = get_all_questions(questions_url)
    save_questions_to_csv(questions_json)
