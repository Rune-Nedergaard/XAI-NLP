import openai

from api_secrets import API_KEY

openai.api_key = API_KEY
prompt = "What would Camus say about the current state of the world?"

response = openai.Completion.create(engine = "text-davinci-003", prompt = prompt, max_tokens=50)


print(response)