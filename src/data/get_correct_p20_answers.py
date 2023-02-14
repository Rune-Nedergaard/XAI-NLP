#This script remedies my mistakes and associates the correct lniks with the correct answer ids.
import requests
import pandas as pd
import concurrent.futures
import ssl
import wget
from tqdm import tqdm
import time

ssl._create_default_https_context = ssl._create_unverified_context

df = pd.read_csv('data/raw/questions_with_answers.csv')

df['answer_id'] = df['answer_id'].fillna(-1).astype('Int64')
#The answer_id column contains the document id for the answer. This is used to get the links to the pdfs.

answer_ids = df['answer_id'].tolist()


links_baseurl = 'https://oda.ft.dk/api/Fil?$inlinecount=allpages&$filter=dokumentid%20eq%20'

def get_filurl(id):
    r = requests.get(links_baseurl + str(int(id)))
    documents = r.json()['value']
    for document in documents:
        if document['filurl'] is not None:
            return document['filurl']
        else: 
            return None


if __name__ == '__main__':
    print('Starting to get links')
    #I save the filurls both to a list and as a new column in the dataframe.
    filurls = []

    #intialize empty column in df called filurl
    df['filurl'] = None

    for id in tqdm(answer_ids, total=len(answer_ids)):
        current = get_filurl(id)
        filurls.append(current)
        #add the filurl to the df for the current answer_id
        df.loc[df['answer_id'] == id, 'filurl'] = current
    
    #save the df to a new csv file
    df.to_csv('data/raw/questions_with_links_new.csv', index=False)
