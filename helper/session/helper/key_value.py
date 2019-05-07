import re


class KeyValue:
    def __init__(self, default):
        if not isinstance(default, dict):
            default = {}
        self._keys = default

    def get(self, key=None):
        if key is not None:
            return self._keys[key]
        return {key: value for key, value in self._keys.items() if key[0] != '$'}

    def add(self, key, value):
        if key is not None:
            if key[-2:] == '[]':
                if key not in self._keys:
                    self._keys[key] = []
                self._keys[key].append(value)
            else:
                self._keys[key] = value

    def extract(self, text):
        regex = re.search(r'{(.*)}', text)
        if regex:
            result = self._keys.get(regex.group(1), '')
            if isinstance(result, list):
                result = ', '.join(result)
            return text[:regex.span(0)[0]] + str(result) + text[regex.span(0)[1]:]
        return text
