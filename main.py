from recentBooks import get_new_books
import requests
import telegramConsts as tc
import os
from dotenv import load_dotenv
import time

debug = False


def main():
    bot_token = get_env_value('BOT_TOKEN')
    channel_id = get_env_value('CHANNEL_ID')

    while True:
        try:
            # get the new books
            new_books = get_new_books(ignore_warnings=True)
            # reverse it, so that we will send the newest books last
            new_books.reverse()
            for book in new_books:
                title = book[0]
                author = book[1]
                url = book[2]
                # this url gives small image.
                # some changes on the url can bring better image
                url = get_better_image(url)
                description = book[3]

                message = create_message(title, author, description)
                if debug:
                    print('sending photo... (message: ' + message + ')')
                send_photo(url, message, bot_token, channel_id)

            # sleep for 10 minutes
            time.sleep(60 * 10)
        except Exception as e:
            print(e)


def send_message(message, bot_token, channel_id):
    requests.get(tc.SEND_MSG.format(bot_token, channel_id, message))


def send_photo(photo_url, caption, bot_token, channel_id):
    requests.get(tc.SEND_PHOTO.format(bot_token, channel_id, photo_url, caption))


def get_env_value(name):
    load_dotenv()
    return os.getenv(name)


def get_better_image(url):
    # there are 2 links to images, the one we have is smaller.
    # so we take the url and ,ake it the url of the bigger image
    try:
        new_url = ''
        url = url.strip('/')

        for i in [0, 1, 2, 6]:
            new_url += url.split('/')[i] + '/'

        new_url = new_url[:new_url.find('150')] + '100' + new_url[new_url.find('150')+3:]
        new_url = new_url[:new_url.rfind('150')] + '100' + new_url[new_url.rfind('150')+3:]

        new_url = new_url.strip('/')

        test = requests.get('http://' + new_url)
        if test.status_code == 200:
            return new_url
        return url
    except Exception:
        return url


def create_message(title, author, description):
    msg = ''
    msg += '<b>' + title + '</b>'
    msg += ' / '
    msg += author
    msg += '\n'
    msg += description
    return msg


if __name__ == '__main__':
    main()
