from bs4 import BeautifulSoup, SoupStrainer
from .exceptions import CannotParsePage

def parse(html_text, parser='html.parser', max_suggestions = 20):
    try:
        soup = BeautifulSoup(html_text, parser)
        entry_body = soup.find('div', class_='entry-body__el')

        suggestion_list = entry_body.find('ol', class_='prefix-block', recursive=False)
        if not suggestion_list:
            raise CannotParsePage()

        suggestion_li_tags = suggestion_list.find_all('li')
        return [extract_suggestion(li_tag) for li_tag in suggestion_li_tags]
    except CannotParsePage:
        raise 
    except Exception as exception:
        raise CannotParsePage('Unknow error') from exception

def extract_suggestion(li_tag):
    return li_tag.find(class_='prefix-item').get_text(strip=True)

    
