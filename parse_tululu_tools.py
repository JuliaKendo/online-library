import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def get_soup(book_url):
    response = requests.get(book_url)
    response.raise_for_status()
    assert book_url == response.url, 'Отсутствует книга на сайте'
    return BeautifulSoup(response.text, 'lxml')


def get_book_atributes(soup):
    book_atributes = {
        'title': '',
        'author': '',
        'img_src': '',
        'book_path': '',
        'comments': [],
        'genres': []
    }
    title_tag = soup.select_one('body div[id=content] h1')
    if title_tag:
        book_name, book_author = re.findall(r'^(.*?)\s::(.*)', title_tag.text)[0]
        book_atributes['title'] = book_name.strip()
        book_atributes['author'] = book_author.strip()

    genre_tag = soup.select('body [id=content] span.d_book a')
    book_atributes['genres'] = [genre.text for genre in genre_tag if genre_tag]

    return book_atributes


def get_book_image(book_url, soup):
    url = re.findall(r'^(.*?)/b', book_url)[0]
    image_link = soup.select_one('.bookimage img')['src']
    if image_link:
        return urljoin(url, image_link)
