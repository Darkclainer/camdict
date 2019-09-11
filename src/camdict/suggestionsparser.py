from bs4 import BeautifulSoup, SoupStrainer
from .exceptions import CannotParsePage

def parse(html_text, parser='html.parser', max_suggestions = 20):
    try:
        strainer = SoupStrainer('ul', class_='hul-u')
        soup = BeautifulSoup(html_text, parser, parse_only=strainer)

        suggestion_list = entry_body.find_all('li', recursive=False)
        if not suggestion_list:
            raise CannotParsePage()

        return [extract_suggestion(li_tag) for li_tag in suggestion_list]
    except CannotParsePage:
        raise 
    except Exception as exception:
        raise CannotParsePage('Unknow error') from exception

def extract_suggestion(li_tag):
    return li_tag.get_text(strip=True)

    
