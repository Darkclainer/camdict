from pathlib import Path
import json
import traceback

import pytest
import requests

from camdict import lemmaparser
from camdict.lemma import Lemma
from camdict.exceptions import CannotParsePage

try:
    import lxml
    parser = 'lxml'
except ModuleNotFoundError:
    parser = 'html.parser'

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'
}

def pytest_addoption(parser):
    parser.addoption('--update-html', 
                     action='store_true', 
                     dest='update_html_files', 
                     help='download html files from dictionary (also rewrite existent)')
    parser.addoption('--only-words', 
                     action='store', 
                     nargs='+', 
                     dest='test_only_words', 
                     help='test only specified words')

def pytest_collect_file(parent, path):
    if path.ext =='.json' and path.dirname.endswith('/json'):
        test_only = parent.config.getoption('test_only_words')
        if not test_only or path.purebasename in test_only:
            return JsonFile(path, parent)

def download_html_file(word_id, path):
    url = 'https://dic' + 'tionary.ca' + 'mbri' + 'dge.org/dictionary/english/' + word_id
    page = requests.get(url, headers=headers)
    with open(path, 'w') as html_file:
        html_file.write(page.text)

class JsonFile(pytest.File):
    def collect(self):
        json_path = Path(self.fspath)
        testname = json_path.stem
        with open(json_path) as json_file:
            try:
                tests_spec = json.load(json_file)
            except json.JSONDecodeError as e:
                yield FailTest(testname, self, 'Can not load test file due to JSONDecodeError.', traceback.format_exc())
                return

        html_path = json_path.parent.parent / 'html' / (json_path.stem + '.html')
        if self.parent.config.getoption('update_html_files'):
            try:
                download_html_file(testname, html_path)
            except Exception as e:
                yield FailTest(testname, self, 'Can not download/save file {}.'.format(html_path), traceback.format_exc())
                return
        try:
            with open(html_path) as html_file:
                lemmas_list = lemmaparser.parse(html_file, parser=parser)
        except FileNotFoundError as e:
            yield FailTest(testname, self, 'File {} does not exists'.format(html_path), traceback.format_exc())
            return
        except CannotParsePage as e:
            yield FailTest(testname, self, 'Can not parse file {}.'.format(html_path), traceback.format_exc())
            return

        try:
            if tests_spec['total'] != len(lemmas_list):
                yield FailTest(testname, self, 
                               'Number of lemmas in the json and in the html file is not equal',
                               '{} != {}'.format(tests_spec['total'], len(lemmas_list)))
                return
            lemmas_info = tests_spec['lemmas']
        except KeyError as e:
            yield FailTest(testname, self, 'Test file has no required attribute.', traceback.format_exc())
            return

        for lemma_info in lemmas_info:
            try:
                lemma_index = lemma_info['index']
                lemma_test_name = '{}[{}]'.format(testname, lemma_index)

                lemma_html = lemmas_list[lemma_index].to_dict()
                lemma_json = lemma_info['lemma']
                for attribute in lemma_json:
                    yield LemmaCompareTest('{}.{}'.format(lemma_test_name, attribute), 
                                           self,
                                           lemma_json,
                                           lemma_html,
                                           attribute)
            except KeyError as e:
                yield FailTest(testname, self, 'Test file has no required attribute.', str(e))
                return



class MyTest(pytest.Item):
    def reportinfo(self):
        return self.fspath, 0, "usecase: %s" % self.name

class FailTest(MyTest):
    def __init__(self, name, parent, msg, exception=None):
        super().__init__(name, parent)
        self.msg = msg
        self.exception = exception

    def runtest(self):
        pytest.fail()

    def repr_failure(self, excinfo):
        return "\n".join(
            [
                self.msg,
                'Error: {}'.format(self.exception) if self.exception else ''
            ]
        )

class SkipTest(MyTest):
    def runtest(self):
        pytest.skip('asdf')

class LemmaCompareTest(MyTest):
    def __init__(self, name, parent, json_lemma, html_lemma, attribute, **kargs):
        super().__init__(name, parent, **kargs)
        self.json_lemma = json_lemma
        self.html_lemma = html_lemma
        self.attribute = attribute

    def repr_failure(self, excinfo):
        return "\n".join(
            [
                'JSON and HTML version of lemma is not equal in attribute "{}". Consider:'.format(self.attribute),
                excinfo.value.args[0],
            ]
        )

    def runtest(self):
        assert self.json_lemma[self.attribute] == self.html_lemma[self.attribute]
