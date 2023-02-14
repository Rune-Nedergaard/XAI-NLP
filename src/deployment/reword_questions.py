import openai

from api_secrets import API_KEY

import openai
import os
import re
import pandas as pd
from pathlib import Path
import glob
from tqdm import tqdm



openai.api_key = API_KEY

df = pd.read_csv('data/translated_questions.csv')
df['answer_id'] = df['answer_id'].astype('Int64')


files = glob.glob('data/translated/*.txt')
files = [os.path.basename(x) for x in files]
answer_ids = [re.sub(r'\.txt', '', x) for x in files]
answer_ids = [x for x in answer_ids if not x.endswith('.tmp')]
answer_ids = [int(x) for x in answer_ids]
mask = df['answer_id'].isin(answer_ids)


examples = df[mask]['translated_questions'].tolist()
answer_ids = df[mask]['answer_id'].tolist()
answer_ids.sort()


# prompt_template = '''Transform questions into simple language that a typical person might use when searching for information online. The revised question should not be written as if it is addressed to the minister.

# Original question 1: Will the minister explain the governments foreign policy in the field of drugs in general and in relation to the negotiations in both the EU circle and in the Commission on Narcotic Drugs prior to the annual meeting in March 2014 and the preceding High Level Segment Session, including which areas and objectives the government prioritizes in the negotiations ?
# Revised question 1: What is the government's foreign policy on drugs?
# ##
# Original question 2: Is it the ministers assessment that the bureaucracy and the plethora of regulations imposed on Danish farmers have gone too far, when e.g. the guidance on fertilization and harmony rules requires 145 pages of review, and the minister considers that there are limits to how large the regulatory burdens and application requirements for e.g. obtaining EU funding, it is reasonable to impose on ordinary people practicing their liberal professions?
# Revised question 2: What is the effect of regulations and requirements on Danish farmers?
# ##
# Original question 3: [INSERT EXAMPLE HERE]
# Revised question 3:'''

#revised zero-shot prompt
prompt_template = '''Transform questions into simple language that a typical person might use when searching for information online. The revised question should not be written as if it is addressed to the minister.

Original question: [INSERT EXAMPLE HERE]
Revised question:'''

reworded_questions = []
failed_answer_ids = []

for example, answer_id in tqdm(zip(examples, answer_ids), total=len(examples)):
    retry = 0
    while retry < 3:
        prompt = prompt_template.replace("[INSERT EXAMPLE HERE]", example)
        try:
            response = openai.Completion.create(engine = "text-davinci-003", prompt = prompt, max_tokens=60, temperature=0, stop=["?", ".", "\n"])
            response_text = response["choices"][0]["text"]
            #removing first space 
            response_text = response_text[1:]+"?"

            filename = str(int(answer_id)) + ".txt"
            with open(os.path.join("data/questions_rephrased", filename), "w") as f:
                f.write(response_text)

            reworded_questions.append(response_text)
            break
        except Exception as e:
            retry += 1
            if retry == 3:
                response_text = "failed"
                failed_answer_ids.append(answer_id)
                reworded_questions.append(None)
                print(f"Request for answer id {answer_id} failed after 3 retries: {e}")
                break
            else:
                print(f"Request for answer id {answer_id} failed, retrying... ({retry}/3)")

if failed_answer_ids:
    print(f"The following answer ids failed: {failed_answer_ids}")


df.sort_values(by=['answer_id'], inplace=True, ascending=True)
df['reworded_questions'] = reworded_questions
df.to_csv("data/reworded_questions.csv", index=False)