import random
from helper.nlp import preprocess, similarity
from helper.knowledge.common import common


class Knowledge:
    def __init__(self, knowledge):
        self._knowledge = preprocess(knowledge, sent_tokenize=True)

    def get(self, text):
        output = self.match_knowledge(text)
        if output is None:
            output = self.match_common(text)
        return output

    def match_knowledge(self, text):
        text = preprocess(text)
        best = {'confidence': 0, 'text': ''}
        for doc, raw in self._knowledge:
            confidence = similarity(text, doc, keyword_confidence=0.7)
            if confidence > best['confidence']:
                best['confidence'] = confidence
                best['text'] = raw
        if best['confidence'] > 0.7:
            return best['text']

    @staticmethod
    def match_common(text):
        text = preprocess(text)
        best = {'confidence': 0, 'text': ''}
        for replies in common:
            for doc in replies[0]:
                doc = preprocess(doc)
                confidence = similarity(text, doc)
                if confidence > best['confidence']:
                    best['confidence'] = confidence
                    best['text'] = replies[1]
        if best['confidence'] > 0.8:
            return random.choice(best['text'])
