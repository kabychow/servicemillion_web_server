from helper.knowledge.knowledge import Knowledge

knowledges = {}


def get(client_id) -> Knowledge:
    return knowledges[client_id]
