import os
import re
import json
import time
import logging
import requests
import argparse
import parse_tululu_tools
from tqdm import tqdm
from urllib import parse
from logger_tools import initialize_logger
from pathvalidate import sanitize_filename
from parse_tululu_tools import raise_for_status
from parse_tululu_category import get_book_urls

logger = logging.getLogger('parsing')


def download_image(url, filename, folder='images'):
    response = requests.get(url)
    raise_for_status(url, response, 'Отсутствует обложка книги на сайте')
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, filename)
    with open(filename, 'wb') as file:
        file.write(response.content)

    return filename


def download_txt(book_url, filename, folder='books'):
    regex_object = re.compile(r'''
                                  ^(.*?)        #группа любые символы с начала строки, соответствующие url
                                  /b            #до символа /b
                                  (.*[^/])      #группа любых символов от символа /b до /, соответствующие id
                                  ''', re.VERBOSE)
    url, book_id = regex_object.findall(book_url)[0]
    url = f'{url}/txt.php?' + parse.urlencode({'id': book_id})
    response = requests.get(url)
    raise_for_status(url, response, 'Отсутствует книга на сайте')

    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, filename)
    with open(filename, 'w') as file:
        file.write(response.text)

    return filename


def download_comments(soup):
    comments_tag = soup.select('.texts .black')
    return [comment.text for comment in comments_tag]


def save_books_attributes(books, dest_folder, json_path):
    json_folder = os.path.join(dest_folder, json_path)
    if json_folder:
        os.makedirs(json_folder, exist_ok=True)
    json_path = os.path.join(json_folder, 'books.json')
    with open(json_path, "w", encoding='utf8') as file:
        json.dump(books, file, ensure_ascii=False)


def load_book(book_url, **kwargs):
    soup = parse_tululu_tools.get_soup(book_url)
    book_attributes = parse_tululu_tools.get_book_attributes(soup)

    if not kwargs['skip_txt']:
        filename = sanitize_filename('%s.txt' % book_attributes['title'])
        book_attributes['book_path'] = download_txt(book_url, filename, kwargs['books_folder'])

    if not kwargs['skip_imgs']:
        url_image = parse_tululu_tools.get_book_image(book_url, soup)
        filename = url_image.split('/')[-1]
        book_attributes['img_src'] = download_image(url_image, filename, kwargs['images_folder'])

    book_attributes['comments'] = download_comments(soup)

    return book_attributes


def next_step(book_urls, pbar):
    try:
        book_url = next(book_urls)
        pbar.update(1)
        return book_url
    except StopIteration:
        return None


def create_parser():
    parser = argparse.ArgumentParser(description='Параметры запуска скрипта')
    parser.add_argument('-s', '--start_page', default=1, help='Начальная страница', type=int)
    parser.add_argument('-e', '--end_page', default=0, help='Конечная страница', type=int)
    parser.add_argument('-f', '--dest_folder', default='', help='Путь к каталогу с результатами парсинга: картинкам, книгам, JSON')
    parser.add_argument('-j', '--json_path', default='', help='Путь к *.json файлу с результатами')
    parser.add_argument('-i', '--skip_imgs', action='store_true', help='Не скачивать картинки')
    parser.add_argument('-t', '--skip_txt', action='store_true', help='Не скачивать книги')
    parser.add_argument('-l', '--log', help='Путь к каталогу с log файлом')
    return parser


def main():
    url = 'http://tululu.org'
    books = []
    parser = create_parser()
    args = parser.parse_args()
    initialize_logger(args.log)
    logger.info('Начало выгрузки книг')

    books_folder = os.path.join(args.dest_folder, 'books')
    images_folder = os.path.join(args.dest_folder, 'images')
    pbar = tqdm(desc="Loading", unit=" books")
    connection_errors = 0
    while True:
        try:
            book_urls = get_book_urls(url, args.start_page, args.end_page)
            book_url = next(book_urls)
            while book_url:
                try:
                    book_attributes = load_book(
                        book_url,
                        books_folder=books_folder,
                        images_folder=images_folder,
                        skip_txt=args.skip_txt,
                        skip_imgs=args.skip_imgs
                    )

                except requests.exceptions.ConnectionError:
                    connection_errors += 1
                    time.sleep(1 if connection_errors < 3 else 300)
                    continue

                except (
                    requests.exceptions.HTTPError,
                    AttributeError, ValueError, TypeError, OSError
                ) as error:
                    book_url = next_step(book_urls, pbar)
                    logger.exception(f'{error}')
                    continue

                else:
                    connection_errors = 0
                    book_url = next_step(book_urls, pbar)
                    books.append(book_attributes)

        except requests.exceptions.ConnectionError:
            connection_errors += 1
            time.sleep(1 if connection_errors < 3 else 300)
            continue

        except requests.exceptions.HTTPError as error:
            raise SystemExit('%s' % error)

        else:
            break

    if books:
        save_books_attributes(books, args.dest_folder, args.json_path)

    logger.info('Книги успешно выгружены')


if __name__ == "__main__":
    main()
