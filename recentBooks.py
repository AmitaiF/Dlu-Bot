import requests
from bs4 import BeautifulSoup
import urllib3
import json
# const values from settings.py
from scrapingConsts import *
# our exceptions, from exceptions.py
from exceptions import *


def get_new_books(ignore_warnings=False):
    if ignore_warnings:
        disable_warnings()

    #  get the main page html
    page = requests.get(URL + MAIN_PAGE, verify=False)
    # make it a BeautifulSoup object
    soup = BeautifulSoup(page.content, 'html.parser')

    # get the "recent books" url (we need to do this
    # because this website creates new url for the "recent
    # books" page for each request)
    recent_page = soup.body.findAll(RECENT_TAG, text=RECENT_TEXT)[0]['href']
    # get the 'recent books' html content
    page = requests.get(URL + recent_page, verify=False)
    # make it a BeautifulSoup object
    soup = BeautifulSoup(page.content, 'html.parser')

    # get all titles
    recent_titles = soup.find_all(TITLES_TAG, class_=TITLES_CLASS)
    # get all authors
    recent_authors = soup.find_all(AUTHOR_TAG, class_=AUTHOR_CLASS)
    # get all the images' links
    recent_images = soup.find_all(IMAGES_TAG, class_=IMAGES_CLASS)

    # get the last book we got in the last time
    # we used this program
    last_book = get_last_book()

    books = []

    # zip the titles and authors, and iterate them
    for book in zip(recent_titles, recent_authors, recent_images):
        # get the book's title
        title_tag = book[0]
        title = title_tag.findChild().text
        # ignore the book in case of non-hebrew title
        if not contains_hebrew(title):
            continue

        if last_book == title:
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


def contains_hebrew(string):
    return any("\u0590" <= c <= "\u05EA" for c in string)


def get_last_book():
    last_book = ''
    # open the json file
    json_file = open('lastBook.json', encoding="utf8")
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
    json_file = open('lastBook.json', 'w', encoding="utf8")
    if json_file.closed:
        raise OpenLastBookFileFailed
    # make dictionary for the 'last book'
    json_data = {}
    json_data['last_book'] = title
    # write it to the file
    json.dump(json_data, json_file)


def disable_warnings():
    urllib3.disable_warnings()


if __name__ == '__main__':
    if DISABLE_WARNINGS:
        disable_warnings()
    new_books = get_new_books()
    print(new_books)
