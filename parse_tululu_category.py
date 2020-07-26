import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from itertools import count


def get_book_urls(url='http://tululu.org', max_page=None):
    for page in count(1):
        url_of_page = '%s/l55/%s' % (url, page)
        response = requests.get(url_of_page)
        response.raise_for_status()
        if not max_page and url_of_page != response.url:
            break
        elif max_page and page > max_page:
            break
        soup = BeautifulSoup(response.text, 'lxml')
        book_tags = soup.find_all('table', class_='d_book')
        for book_tag in book_tags:
            book_ref = book_tag.find('a')['href']
            yield urljoin(url, book_ref)
