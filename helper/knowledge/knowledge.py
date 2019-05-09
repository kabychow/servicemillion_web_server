import json
import random
import os
from helper import nlp


class Knowledge:
    def __init__(self, knowledge):
        self._knowledge = nlp.preprocess(knowledge, sent_tokenize=True)

    def get(self, text):
        output = self.match_knowledge(text)
        if output is None:
            output = self.match_common(text)
        return output

    def match_knowledge(self, text):
        text = nlp.preprocess(text)
        best = {'confidence': 0, 'text': ''}
        for doc, raw in self._knowledge:
            confidence = nlp.similarity(text, doc, keyword_confidence=0.7)
            if confidence > best['confidence']:
                best['confidence'] = confidence
                best['text'] = raw
        if best['confidence'] > 0.7:
            return best['text']

    @staticmethod
    def match_common(text):
        text = nlp.preprocess(text)
        best = {'confidence': 0, 'texts': []}
        with open(os.path.join(os.path.dirname(__file__), 'common.json')) as file:
            for knowledge in json.loads(file.read()):
                for k_input in knowledge['input']:
                    k_input = nlp.preprocess(k_input)
                    confidence = nlp.similarity(text, k_input, keyword_confidence=0.15)
                    if confidence > best['confidence']:
                        best['confidence'] = confidence
                        best['texts'] = knowledge['output']
            if best['confidence'] > 0.8:
                return random.choice(best['texts'])
