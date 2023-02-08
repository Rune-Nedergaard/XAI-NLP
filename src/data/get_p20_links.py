import requests
import pandas as pd
import concurrent.futures
import ssl
import wget

import time



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
        #print(f'Could not download {filename}')
        bad_links.append(filename)


if __name__ == '__main__':
    start_time = time.perf_counter()

    questions = pd.read_csv('data/raw/questions_with_answers.csv')
    answer_ids = questions['answer_id'].tolist()
    links_baseurl = 'https://oda.ft.dk/api/Fil?$inlinecount=allpages&$filter=dokumentid%20eq%20'
    filurls = []
    bad_links = []
    count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        future_filurls = [executor.submit(get_filurls, id) for id in answer_ids]
        for future in concurrent.futures.as_completed(future_filurls):
            id = answer_ids[future_filurls.index(future)]
            current_filurls = future.result()
            count += 1
            if count % 100 == 0:
                current_time = time.perf_counter()
                print(f'Completed {count} requests out of aproximately {len(answer_ids)}')
                print("Time elapsed:", current_time - start_time, "seconds")
                print("Time remaining:", (current_time - start_time) / count * (len(answer_ids) - count), "seconds")
            filurls.append(current_filurls)
            if current_filurls is not None:
                if len(current_filurls) > 0:
                    for url in current_filurls:
                        try:
                            path = 'data/pdfs/' + str(int(id)) + '.pdf'
                            download_pdf(url, path)
                        except:
                            bad_links.append({'id': id, 'url': url})
        #we pickle the filurls to a new csv file
    import pickle
    with open('data/raw/filurls.pickle', 'wb') as f:
        pickle.dump(filurls, f)
    

    questions['filurl'] = filurls
    questions.to_csv('data/raw/questions_with_filurls.csv', index=False)
