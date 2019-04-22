import argparse
import os
import json

from camdict import query

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'
}

def download_and_save_json(word_id, output_path):
    lemmas = query.query_lemma(word_id, headers=headers)
    json_dict = dict(total=len(lemmas),
                     lemmas=[dict(index=i, lemma=lemma.to_dict()) 
                             for i, lemma in enumerate(lemmas)])

    with open(os.path.join(output_path, word_id + '.json'), 'w') as json_file:
        json.dump(json_dict, json_file, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download lemma from dictionary and convert it to json test case')
    parser.add_argument('words', 
                       action='store', 
                       nargs='+', 
                       help='specify word-id')
    parser.add_argument('--path', 
                       action='store', 
                       default='json',
                       dest='output_path')

    args = parser.parse_args()

    for word in args.words:
        download_and_save_json(word, args.output_path)
