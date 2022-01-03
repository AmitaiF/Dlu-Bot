import requests
from bs4 import BeautifulSoup
import urllib3
import json
# const values from settings.py
import scrapingConsts as scraping_consts
# our exceptions, from exceptions.py
from exceptions import *
import os
import sys

session = None
reached_last_book = False


def get_new_books(ignore_warnings=False, debug=False):
    if ignore_warnings:
        disable_warnings()

    global session
    global reached_last_book

    # get the last book we got in the last time
    # we used this program
    last_book = get_last_book()

    # use a seeeion for cookies
    session = requests.Session()

    #  get the main page html
    page = session.get(scraping_consts.URL + scraping_consts.MAIN_PAGE, verify=False)
    # make it a BeautifulSoup object
    soup = BeautifulSoup(page.content, 'html.parser')

    # get the "recent books" url (we need to do this
    # because this website creates new url for the "recent
    # books" page for each request)
    recent_page = soup.body.findAll(scraping_consts.RECENT_TAG, text=scraping_consts.RECENT_TEXT)[0]['href']

    # reached_last_book = False
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
            page = session.get(scraping_consts.URL + recent_page + page_counter, verify=False)
            recent_books_url = page.url
        else:
            page = session.get(recent_books_url + page_counter, verify=False)

        add_new_books(books, page, last_book)

    return books


def add_new_books(books, page, last_book):
    global reached_last_book
    # make it a BeautifulSoup object
    soup = BeautifulSoup(page.content, 'html.parser')

    # get all titles
    titles = soup.find_all(scraping_consts.TITLES_TAG, class_=scraping_consts.TITLES_CLASS)
    # get all authors
    authors = soup.find_all(scraping_consts.AUTHOR_TAG, class_=scraping_consts.AUTHOR_CLASS)
    # get all the images' links
    images = soup.find_all(scraping_consts.IMAGES_TAG, class_=scraping_consts.IMAGES_CLASS)
    # get all links
    links = soup.find_all(scraping_consts.LINK_TAG, class_=scraping_consts.LINK_CLASS)

    # zip the titles and authors, and iterate them
    for book in zip(titles, authors, images, links):
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

        description = get_book_description(book[3])

        books.append((title, author, image_link, description))


def get_book_description(link_element):
    global session
    link = link_element['href']
    page = session.get(scraping_consts.URL + '/' + link)
    soup = BeautifulSoup(page.content, 'html.parser')
    description = soup.find_all(scraping_consts.DESCRIPTION_TAG, class_=scraping_consts.DESCRIPTION_CLASS)[0]
    return description.text


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
    if scraping_consts.DISABLE_WARNINGS:
        disable_warnings()
    new_books = get_new_books(debug=True)
    print_titles(new_books)
