import requests
import pandas as pd
import concurrent.futures
import ssl
import wget
import time
import pickle

ssl._create_default_https_context = ssl._create_unverified_context

'''
This script does the following:
1) Takes the 'answer_id' from the answers csv file and uses it to scrape the links from ODA
2) It then adds the links to the answers csv file and saves it to a new csv file
'''

def get_filurls(answer_id, retries=3):
    filurls = []
    for i in range(retries):
        try:
            r = requests.get(links_baseurl + str(int(answer_id)))
            documents = r.json()['value']
            for document in documents:
                if document['filurl'] is not None:
                    filurls.append(document['filurl'])
            return filurls
        except:
            if i == retries - 1:
                return None

def download_pdf(url, filename):
    try: 
        wget.download(url, filename)
    except:
        bad_links.append(filename)

if __name__ == '__main__':
    start_time = time.perf_counter()

    questions = pd.read_csv('data/raw/questions_with_answers.csv')
    answer_ids = questions['answer_id'].tolist()
    links_baseurl = 'https://oda.ft.dk/api/Fil?$inlinecount=allpages&$filter=dokumentid%20eq%20'
    filurls_dict = {}
    bad_links = []
    count = 0

    for id in answer_ids:
        current_filurls = get_filurls(id)
        filurls_dict[id] = current_filurls
        count += 1
        if count % 100 == 0:
            current_time = time.perf_counter()
            print(f'Completed {count} requests out of approximately {len(answer_ids)}')
            print("Time elapsed:", current_time - start_time, "seconds")
            print("Time remaining:", (current_time - start_time) / count * (len(answer_ids) - count), "seconds")
        if current_filurls is not None:
            if len(current_filurls) > 0:
                for url in current_filurls:
                    try:
                        path = 'data/pdfs/' + str(int(id)) + '.pdf'
                        download_pdf(url, path)
                    except:
                        bad_links.append({'id': id, 'url': url})

    with open('data/raw/filurls.pickle', 'wb') as f:
        pickle.dump(filurls_dict, f)

    #save bad links
    with open('data/raw/bad_links.pickle', 'wb') as f:
        pickle.dump(bad_links, f)

    #save the filurls_dict as a separate pickle
    with open('data/raw/filurls.pickle', 'wb') as f:
        pickle.dump(filurls_dict, f)
    
    all_filurls = [filurls_dict[id] for id in answer_ids]
    questions['filurl'] = all_filurls
    questions.to_pickle('data/raw/questions_with_filurls_newest.pickle')
