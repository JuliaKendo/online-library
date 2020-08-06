import requests
from itertools import count
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parse_tululu_tools import raise_for_status


def get_book_urls(url, min_page=1, max_page=0):
    for page in count(min_page):
        url_of_page = '%s/l55/%s' % (url, page)
        response = requests.get(url_of_page)
        raise_for_status(url_of_page, response, 'Ошибка чтения страниц с сайта. Проверьте максимально допустимое количество страниц.')
        if max_page > 0 and page > max_page:
            break
        soup = BeautifulSoup(response.text, 'lxml')
        book_tags = soup.select('[id=content] .d_book')
        for book_tag in book_tags:
            book_ref = book_tag.select_one('a')['href']
            yield urljoin(url, book_ref)
