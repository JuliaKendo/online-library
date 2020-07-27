import os
import re
import json
import requests
import argparse
import logger_tools
import parse_tululu_tools
from pathvalidate import sanitize_filename
from parse_tululu_category import get_book_urls


def download_image(url, filename, folder='images'):
    response = requests.get(url)
    response.raise_for_status()

    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, filename)
    with open(filename, 'wb') as file:
        file.write(response.content)

    return filename


def download_txt(book_url, filename, folder='books'):
    url, book_id = re.findall(r'^(.*?)/b(.*[^/])', book_url)[0]
    response = requests.get(f'{url}/txt.php', params={'id': book_id})
    response.raise_for_status()

    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, filename)
    with open(filename, 'w') as file:
        file.write(response.text)

    return filename


def download_comments(soup):
    comments_tag = soup.select('.texts .black')
    return [comment.text for comment in comments_tag]


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
    logger_tools.initialize_logger(args.log)

    books_folder = os.path.join(args.dest_folder, 'books')
    images_folder = os.path.join(args.dest_folder, 'images')
    book_urls = get_book_urls(url, args.start_page, args.end_page)
    for book_url in book_urls:
        try:
            soup = parse_tululu_tools.get_soup(book_url)
            book_atributes = parse_tululu_tools.get_book_atributes(soup)

            if not args.skip_txt:
                filename = sanitize_filename('%s.txt' % book_atributes['title'])
                book_atributes['book_path'] = download_txt(book_url, filename, books_folder)

            if not args.skip_imgs:
                url_image = parse_tululu_tools.get_book_image(book_url, soup)
                filename = url_image.split('/')[-1]
                book_atributes['img_src'] = download_image(url_image, filename, images_folder)

            book_atributes['comments'] = download_comments(soup)

        except AssertionError:
            continue

        except AttributeError:
            continue

        else:
            books.append(book_atributes)

    json_folder = os.path.join(args.dest_folder, args.json_path)
    os.makedirs(json_folder, exist_ok=True)
    json_path = os.path.join(json_folder, 'books.json')
    with open(json_path, "w", encoding='utf8') as file:
        json.dump(books, file, ensure_ascii=False)


if __name__ == "__main__":
    main()
