class Messages:
    def __init__(self):
        self._messages = []

    def get(self):
        return self._messages

    def add(self, text):
        self._messages.append(text)
        return text