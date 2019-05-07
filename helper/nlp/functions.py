import re
import spacy

nlp = spacy.load('en_core_web_lg')


def similarity(doc1, doc2, keyword_confidence=0):
    confidence = doc1.similarity(doc2)
    for token in doc1:
        if re.search(r'\b' + re.escape(token.text) + r'\b', doc2.text):
            confidence += keyword_confidence
    return confidence


def match_option(text, what):
    for i in range(len(what)):
        if re.search(r'\b' + what[i] + r'\b', text, flags=re.IGNORECASE):
            return i


def extract(text, what):
    if what == 'name':
        for ent in nlp(text).ents:
            if ent.label_ in ['PERSON']:
                return ent.text
        text = re.sub(r'hello \b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'i am \b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'my name is \b', '', text, flags=re.IGNORECASE)
        if len(text) > 0 and len(text.split()) < 5:
            return text
    elif what == 'email':
        regex = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
        if regex:
            return regex.group()
    elif what == 'phone':
        regex = re.search(r'(\+)?\d{1,24}([- ]\d{1,24}){0,8}', text)
        if regex:
            return regex.group()
    elif what == 'date':
        regex = re.search(r'\b\d{1,4}[-/.]\d{1,4}([-/.]\d{1,4})?\b', text)
        if regex:
            return regex.group()
        for ent in nlp(text).ents:
            if ent.label_ in ['TIME', 'DATE']:
                return ent.text
    else:
        return text


def preprocess(text, sent_tokenize=False):
    if sent_tokenize:
        return [(preprocess(sent.string.strip()), sent.string.strip()) for sent in nlp(text).sents]
    return nlp(' '.join([str(t) for t in nlp(text.lower()) if not t.is_stop]))
