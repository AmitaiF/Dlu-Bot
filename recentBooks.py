import requests
from bs4 import BeautifulSoup
import urllib3
import json
# const values from settings.py
from scrapingConsts import *
# our exceptions, from exceptions.py
from exceptions import *
import os
import sys


def get_new_books(ignore_warnings=False, debug=False):
    if ignore_warnings:
        disable_warnings()

    # get the last book we got in the last time
    # we used this program
    last_book = get_last_book()

    # use a seeeion for cookies
    session = requests.Session()

    #  get the main page html
    page = session.get(URL + MAIN_PAGE, verify=False)
    # make it a BeautifulSoup object
    soup = BeautifulSoup(page.content, 'html.parser')

    # get the "recent books" url (we need to do this
    # because this website creates new url for the "recent
    # books" page for each request)
    recent_page = soup.body.findAll(RECENT_TAG, text=RECENT_TEXT)[0]['href']

    reached_last_book = False
    books = []

    page_counter = '&Page=0'
    recent_books_url = ''

    while not reached_last_book:
        # every iteration we increase the page counter
        # in order to go through all the pages
        # until we reach the last book
        page_counter = inc_page_counter(page_counter)

        if debug:
            print('getting', page_counter)

        if recent_books_url == '':
            # get the 'recent books' html content
            page = session.get(URL + recent_page + page_counter, verify=False)
            recent_books_url = page.url
        else:
            page = session.get(recent_books_url + page_counter, verify=False)

        # make it a BeautifulSoup object
        soup = BeautifulSoup(page.content, 'html.parser')

        # get all titles
        recent_titles = soup.find_all(TITLES_TAG, class_=TITLES_CLASS)
        # get all authors
        recent_authors = soup.find_all(AUTHOR_TAG, class_=AUTHOR_CLASS)
        # get all the images' links
        recent_images = soup.find_all(IMAGES_TAG, class_=IMAGES_CLASS)

        # zip the titles and authors, and iterate them
        for book in zip(recent_titles, recent_authors, recent_images):
            # get the book's title
            title_tag = book[0]
            title = title_tag.findChild().text
            # ignore the book in case of non-hebrew title
            if not contains_hebrew(title):
                continue

            if last_book == title:
                # we reached the last book
                reached_last_book = True
                # set the 'last book' to the newest book we got now
                if len(books) > 0:
                    set_new_book(books[0][0])
                break

            # get the book's author
            author_tag = book[1]
            author = author_tag.findChild().text

            # get the book's image link
            image_link = book[2]['data-original']

            books.append((title, author, image_link))

    return books


def inc_page_counter(page_counter):
    page, num = page_counter.split('=')
    num = str(int(num) + 1)
    return '='.join([page, num])


def contains_hebrew(string):
    return any("\u0590" <= c <= "\u05EA" for c in string)


# get full path to the current dir
here = os.path.abspath(os.path.dirname(__file__))
# add slashes according to the os platform
if sys.platform == 'linux':
    here += '/'
elif sys.platform == 'win32':
    here += '\\'


def get_last_book():
    last_book = ''
    # open the json file
    json_file = open(here + 'lastBook.json', encoding="utf8")
    if json_file.closed:
        raise OpenLastBookFileFailed
    # load the data
    json_data = json.load(json_file)

    json_file.close()

    # get the last book
    last_book = json_data['last_book']
    return last_book


def set_new_book(title):
    # open the json file for writing
    json_file = open(here + 'lastBook.json', 'w', encoding="utf8")
    if json_file.closed:
        raise OpenLastBookFileFailed
    # make dictionary for the 'last book'
    json_data = {}
    json_data['last_book'] = title
    # write it to the file
    json.dump(json_data, json_file)


def disable_warnings():
    urllib3.disable_warnings()


def print_titles(books):
    for book in books:
        print(book[0])


if __name__ == '__main__':
    if DISABLE_WARNINGS:
        disable_warnings()
    new_books = get_new_books(debug=True)
    print_titles(new_books)
