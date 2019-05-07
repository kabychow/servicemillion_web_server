class Queue:
    def __init__(self, name, email, question):
        self.name = name
        self.email = email
        self.question = question
        self.socket = None
        self.agent_socket = None
