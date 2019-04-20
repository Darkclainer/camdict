import re
import logging

from bs4 import BeautifulSoup, SoupStrainer, Tag

from lemma import Lemma
import ipahelper

logger = logging.getLogger(__name__)

__all__ = ['parse']

class CannotParsePage(Exception): pass
class UnknownIpa(CannotParsePage): pass

def deal_with_newlines(s):
    s = s.replace('\n', ' ')
    s = re.sub('\s\s+', ' ', s)
    return s.strip()

def format_definition(s):
    s = deal_with_newlines(s)
    if s[-1] == ':':
        s = s[:-1]
    return s

def make_lemma(info):
    lemma = Lemma(info['lemma'], 
                  info['part_of_speech'],
                  info['language'])

    lemma.transcriptions = dict(info['transcriptions'])
    lemma.definition = info.get('definition', None)
    lemma.guide_word = info.get('guide_word', None)
    lemma.alternative_form = info.get('alternative_form', None)
    if 'examples' in info:
        lemma.examples = list(info['examples'])
    lemma.gc = set(info['gc'])

    return lemma

def parse(page_content_html, parser = 'html.parser'):
    entry_content_strainer = SoupStrainer(id='entryContent')
    soup = BeautifulSoup(page_content_html, parser, parse_only=entry_content_strainer)

    lemmas_list = list(get_lemmas_from_soup(soup))

    return lemmas_list

def get_lemmas_from_soup(soup):
    page = soup.find('div', class_='page')
    if not page:
        raise CannotParsePage('<div class="page"> is absent! Can not continue, because it must contain sorter')
    sorter = soup.find('div', attrs={'data-type':'sorter'})
    if not sorter:
        raise CannotParsePage('<div data-type="sorter"> is absent! It must containt word datasets!')
    word_datasets = sorter.findAll(class_='dictionary', recursive=False)

    for word_dataset in word_datasets:
        yield from get_lemmas_from_dataset(word_dataset)

data_id_to_language = {
        'cald4': 'british',
        'cacd': 'american-english',
        'cbed': 'business-english'
}
def get_language_of_dataset(word_dataset):
    if word_dataset.has_attr('data-wrodlist-dataset'):
        return word_dataset['data-wordlist-dataset']
    elif word_dataset.has_attr('data-id'):
        data_id = word_dataset['data-id']
        language = data_id_to_language.get(data_id)
        if language is None:
            raise CannotParsePage('Unkown data-id: {}'.format(data_id))
        return language

    logger.debug('Can not determine word_dataset language')
    return None

def get_lemmas_from_dataset(word_dataset):
    lemmas_shared = {} # shared data between lemas
    lemmas_shared['language'] = get_language_of_dataset(word_dataset)

    entry_body_tags = word_dataset.find_all(class_='entry-body')
    for entry_body_tag in entry_body_tags:
        yield from get_lemmas_from_entry_body(entry_body_tag, lemmas_shared)

def get_lemmas_from_entry_body(entry_body_tag, lemmas_shared):
    # find all wordTags - big frame with transcription and other. Distinguished by part of speech may be
    entry_body__el_tags = entry_body_tag.find_all(class_='entry-body__el', recursive=False) 
    for entry_body__el in entry_body__el_tags:
        # this div has phrasal verbs and doesn't have general words
        relativ_div = entry_body__el.find(class_='relativDiv', recursive=False)
        if relativ_div:
            yield from get_lemmas_from_relativ_div(relativ_div, lemmas_shared)
        else:
            yield from get_lemmas_from_entry_body__el(entry_body__el, lemmas_shared)

def get_lemmas_from_entry_body__el(entry_body__el, lemmas_shared):
    pos_header = entry_body__el.find(class_='pos-header', recursive=False)

    # create copy of dictionary, because this information can differ
    lemmas_shared = dict(lemmas_shared)
    # update part_of_speach, transcriptions, lemma letters and etc.
    lemmas_shared.update(extract_lemmas_data_from_header(pos_header))

    pos_body = entry_body__el.find(class_='pos-body', recursive=False)
    sense_blocks = pos_body.find_all(class_='sense-block', recursive=False)
    for sense_block in sense_blocks:
        yield from get_lemmas_from_sense_block(sense_block, lemmas_shared)

# --- pos-header extraction section ---
def extract_lemmas_data_from_header(pos_header):
    info = {}

    di_title = pos_header.find(class_='di-title', recursive=False)
    if not di_title:
        raise CannotParsePage('pos-header does not have <div class="h3 di-title..."> element with headword and etc')

    headword = di_title.find(class_='headword')
    info['lemma'] = headword.get_text(strip=True)
    info['part_of_speech'] = extract_pos_with_headword(headword)
    info['transcriptions'] = extract_transcriptions_from_pos_header(pos_header) 
    return info

def extract_pos_with_headword(headword):
    posgram = headword.find_next_sibling('span', class_='posgram')
    if posgram:
        return posgram.get_text(strip=True)
    else:
        return 'unknown'

def extract_transcriptions_from_pos_header(pos_header):
    pron_tags = pos_header.find_all('span', class_='pron')
    transcriptions = {region: transcription 
                      for region, transcription in get_transcriptions_from_pron_tags(pron_tags)}
    return transcriptions

def get_transcriptions_from_pron_tags(pron_tags):
    for pron_tag in pron_tags:
        region_tag = pron_tag.find_previous_sibling('span', class_='region')
        ipa_tags = pron_tag.find_all('span', class_='ipa', recursive=False)
        if not region_tag or not ipa_tags:
            continue

        region = region_tag.get_text(strip=True).lower()
        transcription = [extract_transcription_from_ipa(ipa_tag) for ipa_tag in ipa_tags]
        yield region, transcription

def extract_transcription_from_ipa(ipa_tag):
    parts = []
    for child in ipa_tag.children:
        if isinstance(child, Tag):
            if child.has_attr('class') and 'sp' in child['class']:
                parts.append(ipahelper.superscript(child.get_text(strip=True)))
            else:
                raise UnknownIpa()
        else:
            parts.append(str(child))
    return ''.join(parts)
# --- pos-header extraction section --- END

def get_lemmas_from_sense_block(sense_block, lemmas_shared):
    lemmas_shared = dict(lemmas_shared)
    lemmas_shared['guide_word'] = extract_guide_word_from_sense_block(sense_block)

    sense_bodies = sense_block.find_all(class_='sense-body', recursive=False)
    for sense_body in sense_bodies:
        yield from get_lemmas_from_sense_body(sense_body, lemmas_shared)

def extract_guide_word_from_sense_block(sense_block):
    txt_block = sense_block.find(class_='txt-block', recursive=False)
    if not txt_block:
        return None

    guide_word = txt_block.find(class_='guideword', recursive=False)
    if not guide_word:
        return None

    return guide_word.span.get_text(strip=True).lower()

def get_lemmas_from_sense_body(sense_body, lemmas_shared):
    for child in sense_body.find_all('div', recursive=False):
        if 'def-block' in child['class']:
            yield get_lemma_from_def_block(child, lemmas_shared)
        elif 'phrase-block' in child['class']:
            yield from get_lemmas_from_phrase_block(child, lemmas_shared)

# --- def-block lemma extraction section ---
def get_lemma_from_def_block(def_block, lemmas_shared):
    lemmas_shared = dict(lemmas_shared)
    def_head = def_block.find(class_='def-head', recursive=False)
    lemmas_shared['definition'] = extract_definition_from_def_head(def_head)

    def_info = def_head.find(class_='def-info', recursive=False)
    if def_info:
        lemmas_shared['gc'] = extract_gc_from_def_info(def_info)
        lemmas_shared['alternative_form'] = extract_alternative_form_from_def_info(def_info)

    lemmas_shared['examples'] = [example for example in get_examples_from_def_block(def_block)]

    return make_lemma(lemmas_shared)

def extract_definition_from_def_head(def_head):
    def_tag = def_head.find('b', class_='def', recursive=False)
    return format_definition(def_tag.get_text())

def extract_gc_from_def_info(def_info):
    gc_tags = def_info.find('span', class_='gcs')
    if not gc_tags:
        return {}
    return {gc.get_text(strip=True) for gc in gc_tags.find_all(class_='gc', recursive=False)}

def extract_alternative_form_from_def_info(def_info):
    v_tag = def_info(class_='v')
    if not v_tag:
        return None
    return v_tag.get_text(strip=True)

def get_examples_from_def_block(def_block):
    def_body = def_block.find(class_='def-body', recursive=False)
    if not def_body:
        return
    for examp_tag in def_body.find_all(class_='examp', recursive=False):
        yield deal_with_newlines(examp_tag.get_text())
# --- def-block lemma extraction section --- END

# --- phrase-block lemma extraction section ---
def get_lemmas_from_phrase_block(phrase_block, lemmas_info):
    lemmas_info = dict(lemmas_info)
    phrase_head = phrase_block.find(class_='phrase-head', recursive=False)
    lemmas_info['alternative_form'] = phrase_head.span.b.get_text() # class="phrase"

    phrase_body = phrase_block.find(class_='phrase-body', recursive=False)
    def_blocks = phrase_body.find_all(class_='def-block', recursive=False)
    for def_block in def_blocks:
        yield get_lemma_from_def_block(def_block, lemmas_info)
# --- phrase-block lemma extraction section --- END

def get_lemmas_from_relativ_div(relativ_div, lemmas_info):
    for child in relativ_div.find_all('div', recursive=False):
        if 'pv-block' in child['class']:
            yield from get_lemmas_from_pv_block(child, lemmas_info)
        elif 'idiom-block' in child['class']:
            yield from get_lemmas_from_idiom_block(child, lemmas_info)

# --- pv-block lemma extraction section ---
def get_lemmas_from_pv_block(pv_block, lemmas_info):
    lemmas_info = dict(lemmas_info)
    lemmas_info.update(extract_lemmas_info_from_pv_block(pv_block))

    pv_body = pv_block.find(class_='pv-body', recursive=False)
    sense_blocks = pv_body.find_all(class_='sense-block')
    for sense_block in sense_blocks:
        yield from get_lemmas_from_sense_block(sense_block, lemmas_info)

def extract_lemmas_info_from_pv_block(pv_block):
    info = {}
    di_title = pv_block.find(class_='di-title', recursive=False)
    info['lemma'] = di_title.get_text(strip=True)

    di_info = pv_block.find(class_='di-info', recursive=False)
    pos_header = di_info.find(class_='pos-header', recursive=False)
    anc_info_head = pos_header.find(class_='anc-info-head', recursive=False)
    pos_tag = anc_info_head.find(class_='pos', recursive=False)
    info['part_of_speech'] = pos_tag.get_text(strip=False)
    info['transcriptions'] = extract_transcriptions_from_pos_header(pos_header)
    return info
# --- pv-block lemma extraction section --- END

# --- idiom-block lemma extraction section ---
def get_lemmas_from_idiom_block(idiom_block, lemmas_info):
    lemmas_info = dict(lemmas_info)
    lemmas_info['lemma'] = extract_headword_from_idiom_block(idiom_block)
    lemmas_info['part_of_speech'] = 'idiom'
    lemmas_info['transcriptions'] = {}

    idiom_body = idiom_block.find(class_='idiom-body', recursive=False)
    sense_blocks = idiom_body.find_all(class_='sense-block', recursive=False)
    for sense_block in sense_blocks:
        yield from get_lemmas_from_sense_block(sense_block, lemmas_info)

def extract_headword_from_idiom_block(idiom_block):
    di_title = idiom_block.find(class_='di-title', recursive=False)
    headword = di_title.find(class_='headword', recursive=False)
    return headword.get_text(strip=True)
# --- idiom-block lemma extraction section --- END
