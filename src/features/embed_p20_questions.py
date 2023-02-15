"""
This scripts embeds the rephrased questions and stores them as a numpy array
"""

import numpy 
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-mpnet-base-v2')
from sklearn.metrics.pairwise import cosine_similarity
import os
import glob
import re

#Encoding all questions stored in txt files in data/questions_rephrased
import os
import glob
import numpy as np
import pickle

def encode_dataset():
    # Load all questions from the data/questions_rephrased folder
    questions = []
    for filename in glob.glob(os.path.join('data/questions_rephrased', '*.txt')):
        with open(filename, 'r', encoding='utf-8') as fIn:
            try:
                question_text = fIn.read()
            except UnicodeDecodeError:
                # Try opening the file with ISO-8859-1 encoding
                fIn = open(filename, 'r', encoding='iso-8859-1')
                question_text = fIn.read()
                fIn.close()
            # Get the basename of the file
            basename = os.path.basename(filename)
            # Append the question and its basename to the list of questions
            questions.append((question_text, basename))
    print("Embedding %d questions" % len(questions))
    # Compute embedding for each question
    embeddings = model.encode([q[0] for q in questions], convert_to_tensor=False)

    # Create a dictionary to store the embeddings, corresponding information, and basenames
    data = {}
    for i, filename in enumerate(glob.glob(os.path.join('data/questions_rephrased', '*.txt'))):
        with open(filename, 'r', encoding='utf-8') as fIn:
            try:
                question_text = fIn.read()
            except UnicodeDecodeError:
                # Try opening the file with ISO-8859-1 encoding
                fIn = open(filename, 'r', encoding='iso-8859-1')
                question_text = fIn.read()
                fIn.close()
            data[i] = {'text': question_text, 'embedding': embeddings[i], 'basename': os.path.basename(filename)}


    # Save the dictionary as a file using pickle
    with open('data/questions_embedded/embeddings.pkl', 'wb') as fOut:
        pickle.dump(data, fOut)


if __name__ == '__main__':
    encode_dataset()
