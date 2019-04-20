import json 

class Lemma:
    def __init__(self, lemma, part_of_speech='unknown', language='unknown'):
        self.lemma = lemma
        self.part_of_speech = part_of_speech
        self.language = language
        self.transcriptions = {}

        self.definition = None
        self.guide_word = None
        self.alternative_form = None
        self.examples = []
        self.gc = {}

    def encode(self, **kargs):
        return json.dumps(self, cls=LemmaJSONEncoder, **kargs)

    @staticmethod
    def decode(json_repr, **kargs):
        return json.loads(json_repr, cls=LemmaJSONDecoder, **kargs)

    def __repr__(self):
        return '<Lemma {}.{}>'.format(self.lemma, self.part_of_speech)


class LemmaJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Lemma):
            return {
                'lemma': obj.lemma,
                'part_of_speech': obj.part_of_speech,
                'language': obj.language,
                'transcriptions': obj.transcriptions,
                'definition': obj.definition,
                'guide_word': obj.guide_word,
                'alternative_form': obj.alternative_form,
                'examples': obj.examples,
                'gc': list(obj.gc)
            }
        else:
            return json.JSONEncoder.default(self, obj)

class LemmaJSONDecoder(json.JSONDecoder):
    def decode(self, s):
        lemma_dict = json.JSONDecoder.decode(self, s)
        try:
            lemma = Lemma(lemma_dict['lemma'], lemma_dict['part_of_speech'], lemma_dict['language'])
            lemma.transcriptions = lemma_dict['transcriptions']
            lemma.definition = lemma_dict['definition']
            lemma.guide_word = lemma_dict['guide_word']
            lemma.alternative_form = lemma_dict['alternative_form']
            lemma.examples = lemma_dict['examples']
            lemma.gc = set(lemma_dict['gc'])
            return lemma
        except KeyError as e:
            raise json.JSONDecodeError() from e
