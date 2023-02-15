import openai

from api_secrets import API_KEY

openai.api_key = API_KEY

"""
This script does the following:
1) Takes a prompt from the user, which is any question about Danish politics
2) Finds the K nearest neighbors of the question in the question embedding space
3) Takes the answers to the top K questions, checks if these have already been processed,
otherwise it processes them by extracting the facts from these and saves them in txt files
4) Takes the facts from the top K answers and uses them as context to generate a new answer to the user question
"""


prompt = "What would Camus say about the current state of the world?"

response = openai.Completion.create(engine = "text-davinci-003", prompt = prompt, max_tokens=50)


print(response)