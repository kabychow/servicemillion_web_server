from helper import database
from helper.knowledge.knowledge import Knowledge

knowledges = {}

for api_key, knowledge in database.get_all_knowledge():
    knowledges[api_key] = Knowledge(knowledge)


def get(api_key, text):
    return knowledges[api_key].get(text)
