import requests
from requests.status_codes import codes as http_codes
import urllib

from . import lemmaparser
from . import suggestionsparser
from .exceptions import QueryRefused, QueryUnknownResponce

camdict_word_url = 'https://dictionary.cambridge.org/dictionary/english/'
camdict_suggestion_url = 'https://dictionary.cambridge.org/spellcheck/english/'
camdict_query_url = 'https://dictionary.cambridge.org/search/english/direct/'

def extract_last_path_url(url):
    path = urllib.parse.urlparse(url).path
    return path.rpartition('/')[2]

def extract_query_url(url):
    query = urllib.parse.urlparse(url).query
    return urllib.parse.parse_qs(query)['q'][0]

def update_session(session=None, headers=None):
    if not session:
        session = requests.Session()
    if headers:
        session.headers.update(headers)
    return session


def query(lemma, session=None, headers=None, **kargs):
    session = update_session(session, headers)

    response = session.get(camdict_query_url, 
                           params=dict(q=lemma), 
                           allow_redirects=False, 
                           **kargs)

    if response.status_code != http_codes.found:
        raise QueryRefused('Status code: {}'.format(response.status_code))

    redirect = response.headers['Location']

    if redirect.startswith(camdict_word_url):
        return 'word_id', extract_last_path_url(redirect)
    elif redirect.startswith(camdict_suggestion_url):
        return 'suggestions', extract_query_url(redirect)
    else:
        raise QueryUnknownResponce(redirect)

def query_lemma(word_id, session=None, headers=None, parser='html.parser', **kargs):
    session = update_session(session, headers)

    response = session.get(urllib.parse.urljoin(camdict_word_url, word_id), 
                           allow_redirects=False,
                           **kargs)
    if response.status_code != http_codes.ok:
        raise QueryRefused('Status code: {}'.format(response.status_code))

    return lemmaparser.parse(response.content, parser=parser)

def query_suggestions(lemma, session=None, headers=None, parser='html.parser', **kargs):
    session = update_session(session, headers)

    response = session.get(camdict_suggestion_url,
                           params=dict(q=lemma),
                           allow_redirects=False,
                           **kargs)

    if response.status_code != http_codes.ok:
        raise QueryRefused('Status code: {}'.format(response.status_code))

    return suggestionsparser.parse(response.content, parser=parser)
