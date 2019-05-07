class Sequence:
    def __init__(self, action):
        self._sequence = [action]

    def current(self, key=None):
        if key is not None:
            return self._sequence[-1][key]
        return self._sequence[-1]

    def add(self, action):
        if action is not None:
            if isinstance(action, int):
                action = self._sequence[len(self._sequence) + action - 1]
            self._sequence.append(action)
        else:
            self._sequence = self._sequence[0:1]
