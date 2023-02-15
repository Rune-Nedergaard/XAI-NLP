import openai

from api_secrets import API_KEY

openai.api_key = API_KEY
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-mpnet-base-v2')
from sklearn.metrics.pairwise import cosine_similarity
import os
import glob
import re
from pathlib import Path
import numpy as np
import pickle
import math
import nltk
nltk.download('punkt')



"""
This script does the following:
1) Takes a prompt from the user, which is any question about Danish politics
2) Finds the K nearest neighbors of the question in the question embedding space
3) Takes the answers to the top K questions, checks if these have already been processed,
otherwise it processes them by extracting the facts from these and saves them in txt files
4) Takes the facts from the top K answers and uses them as context to generate a new answer to the user question
5) Does the above, but translating to a English and then back to Danish
6) It should also provide the links to the questions and some info about the questions
"""



#prompt = "What would Camus say about the current state of the world?"

#response = openai.Completion.create(engine = "text-davinci-003", prompt = prompt, max_tokens=50)





def find_nearest_questions(user_question, encoded_corpus, top_k=10):
    # Load the embeddings and corresponding text from the file
    with open('data/questions_embedded/embeddings.pkl', 'rb') as fIn:
        data = pickle.load(fIn)

    # Extract the embeddings, corresponding text, and basenames from the dictionary
    embeddings = []
    text = []
    basenames = []
    answer_ids = []
    for i in range(len(data)):
        embeddings.append(data[i]['embedding'])
        text.append(data[i]['text'])
        filename = data[i].get('basename')
        if filename:
            basenames.append(os.path.splitext(os.path.basename(filename))[0])
        else:
            basenames.append(str(i))
        answer_id = data[i].get('answer_id')
        if answer_id:
            answer_ids.append(answer_id)
        else:
            answer_ids.append(None)

    # Encode the new question
    encoded_question = model.encode([user_question])[0]

    # Compute the cosine similarities between the new question and the encoded corpus
    cosine_similarities = np.dot(embeddings, encoded_question) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(encoded_question))

    # Sort the cosine similarities in descending order
    nearest_questions_indices = cosine_similarities.argsort()[::-1][:top_k]

    # Retrieve the corresponding text, basename, and answer_id for the nearest questions
    nearest_questions = []
    for i in nearest_questions_indices:
        nearest_questions.append((text[i], basenames[i], answer_ids[i]))

    return nearest_questions





def get_facts(nearest_questions, idx):
    """
    This function takes the id of a question, checks if facts have been extracted for the answer to this question,
    if it has, it returns these, otherwise it extracts the facts from the answer and saves them in a txt file
    """

    prompt_template ="""Provide a comprehensive summary of the text below using bullet points and a high level of technical detail. You may paraphrase the original wording to improve the summary's comprehensibility, while ensuring that the important content and actors involved are accurately represented
    Text:
    ###
    [TEXT]
    ###
    """
    answer_id = nearest_questions[idx][1]
    # First check if the facts have already been extracted
    if Path(f"data/answer_facts/{answer_id}.txt").is_file():
        print(f"Answer {answer_id} already processed, loading facts")
        with open(f"data/answer_facts/{answer_id}.txt", "r") as f:
            facts = f.read()
            return facts
    else:
        #load the answer
        print(f"Answer {answer_id} not processed, extracting facts")
        try:
            with open(f"data/translated/{str(answer_id)}.txt", "r") as f:
                answer_text = f.read()
        except:
            print(f"No answer found for §20 question with id {answer_id}")
            answer_text = ""

        # Check if the text length is more than 2000 tokens
        if len(nltk.word_tokenize(answer_text)) > 2000:
            # Split text into chunks of equal length that are less than 2000 tokens long
            num_chunks = math.ceil(len(nltk.word_tokenize(answer_text)) / 2000)
            chunk_size = math.ceil(len(nltk.word_tokenize(answer_text)) / num_chunks)
            text_chunks = [answer_text[i:i+len(' '.join(nltk.word_tokenize(answer_text[i:i+chunk_size])))].strip() for i in range(0, len(answer_text), chunk_size)]
        else:
            text_chunks = [answer_text]
        # Initialize list to store facts from each chunk
        fact_list = []
        retries = 0
        # Loop through each chunk of text and send as individual prompt to OpenAI
        for i, text_chunk in enumerate(text_chunks):
            while retries < 3:
                try:
                    prompt = prompt_template.replace("[TEXT]", text_chunk)
                    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=2000)

                    # Save the facts from this chunk to the list
                    fact_list.append(response["choices"][0]["text"])
                    break
                except:
                    if retries == 2:
                        print(f"Error with chunk {i} of answer {answer_id}, skipping")
                        break
                    retries += 1
                    print(f"Error with chunk {i} of answer {answer_id}, retrying ({retries}/3)")
                    continue
                    

        # Combine the facts from all chunks into a single string
        facts = "\n".join(fact_list)
        """THE ANSWERS ARE WRITTEN TWICE FIX THIS"""
        # Saving the facts
        with open(f"data/answer_facts/{answer_id}.txt", "w") as f:
            f.write(facts)

        return facts



def generate_answer(user_question, nearest_questions):
    """
    This function takes the user question, the nearest questions and answers, and generates an answer to the user question
    """
    #Getting the facts from the answers
    facts = []
    for i in range(len(nearest_questions)):
        facts.append(get_facts(nearest_questions, i))


    #Get a single string from facts list using \n as separator
    #facts_string = "\n".join(facts)

    #Generating the answer
    prompt_template = '''You are a chatbot designed to answer citizens' questions regarding politics.
    You will be provided a set of facts, some of which may be relevant to answering the question.
    Your answer should strive to be nuanced and comprehensive, weighing both sides of the issue if applicable.
    Carefully review the set of facts provided and consider which of them can help you answer the citizen's question.
    If the facts provide some clues, use them to provide your answer. Reference relevant sources of evidence to support your argument, making note of relevant dates. 
    If the facts don't provide enough information, explain why not and suggest what additional information or data would be needed to adequately address the question.

    Facts: 
    """
    [CONTEXT]
    """
    Citizen's question: "[QUESTION]"
    Answer:'''
    prompt = prompt_template.replace("[CONTEXT]", "\n".join(facts)).replace("[QUESTION]", user_question)
    response = openai.Completion.create(engine = "text-davinci-003", prompt = prompt, max_tokens=2000, temperature=0.2)
    complete_text = prompt+response["choices"][0]["text"]
    return response["choices"][0]["text"], complete_text
    

if __name__ == '__main__':
    user_question = input("What would you like to ask?: ")
    encoded_corpus = np.load('data/questions_embedded/embeddings.npy')

    nearest_questions = find_nearest_questions(user_question, encoded_corpus, top_k=5)

    print(f"Nearest questions to {user_question} are:")
    for i in nearest_questions:
        print(i[0], i[1])
    
    #Getting indices of the nearest questions
    indices = [i[1] for i in nearest_questions]

    #Getting the answers to the nearest questions
    #Could just use answer_id directly, but this is fine
    for idx in range(len(nearest_questions)):
        print(f"Getting facts for §20 question number {idx+1}/{len(nearest_questions)}")
        get_facts(nearest_questions,idx)

    answers = []
    for i in indices:
        try:
            with open(f"data/answer_facts/{i}.txt", "r") as f:
                answers.append(f.read())
        except:
            print(f"Answer for question {i} not found")
    
    response, complete_text = generate_answer(user_question, nearest_questions)
    print(response)
    #save the response and complete text
    try:
        with open("data/generated_answers/response_text/response.txt", "w") as f:
            f.write(user_question)
        with open("data/generated_answers/complete_text/complete_text.txt", "w") as f:
            f.write(user_question)
    except:
        print("Error saving response and complete text")
    

