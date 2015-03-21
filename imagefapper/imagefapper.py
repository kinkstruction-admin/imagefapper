"""
Usage:  imagefapper <gallery_url>
        imagefapper --version
        imagefapper --help

Arguments:
    <gallery_url>           The URL to an imagefap gallery page.

Options:
    --version, -v           Display the version and quit
    --help, -h              Display this lovely help message and quit.
"""

import os
import re
import requests
import shutil
import six
import threading

from docopt import docopt
from six.moves import urllib_parse
from warnings import warn
from ._version import __version__

from html.parser import HTMLParser


def main():

    args = docopt(__doc__, version=__version__)

    print(args)

    gallery = Gallery(url=args["<gallery_url>"])

    gallery.download()


class ScraperException(Exception):
    pass


class Gallery(object):

    def __init__(self, url, max_threads=10, base_directory="."):
        self.url = url

        if not isinstance(max_threads, six.integer_types) or max_threads <= 0:
            raise ValueError("max_threads must be a positive integer")

        self.max_threads = max_threads
        self.base_directory = base_directory
        self.id = url.split("/")[-2]

        assert re.match("^\d+$", self.id), \
            "Unexpected gallery id: {}".format(self.id)

        parsed = urllib_parse.urlparse(url)

        self.base_url = url
        self.full_page_url = url

        self.photo_pages = []
        self.image_links = []

        if parsed.query:
            query_parts = dict(urllib_parse.parse_qsl(parsed.query))
            self.base_url = re.sub(
                "\?$", "", parsed.geturl().replace(parsed.query, ""))

            if "gid" in query_parts:
                assert query_parts.get("gid") == self.id, \
                    "gid from URL and gid from query don't match ({},{})".format(self.id, query_parts.get("gid"))

        self.full_page_url = "{}?gid={}&view=2".format(self.base_url, self.id)

        self.name = self.base_url.split("/")[-1].replace("-", " ")

        self.directory = os.path.join(self.base_directory, self.name.replace(" ", "_").lower())

        if not os.path.exists(self.directory):
            os.mkdir(self.directory)
        elif not os.path.isdir(self.directory):
            raise ValueError("The file '{}' exists and is not a directory".format(self.directory))

    def get_photo_pages(self):

        response = requests.get(self.full_page_url)

        if response.status_code != 200:
            raise ScraperException(
                "For url '{}', received status code {}".format(self.full_page_url, response.status_code))

        html = response.text

        scraper = PhotoPageScraper()
        scraper.feed(html)

        self.photo_pages = scraper.photo_pages

    def get_image_links(self):
        # TODO: Make this threaded as well, since it's a bottleneck.
        if not self.photo_pages:
            self.get_photo_pages()

        for url in self.photo_pages:

            response = requests.get(url)

            if response.status_code != 200:
                raise ScraperException(
                    "For url '{}', received status code {}".format(self.full_page_url, response.status_code))

            html = response.text

            scraper = ImageLinkScraper()
            scraper.feed(html)

            for link in scraper.image_links:
                if link not in self.image_links:
                    self.image_links.append(link)

    def download(self):
        semaphore = threading.Semaphore(self.max_threads)

        if not self.image_links:
            self.get_image_links()

        for i, url in enumerate(self.image_links):
            ImageDownloader(semaphore, url, i, self.directory).start()


class PhotoPageScraper(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)

        self.photo_pages = []

    def handle_starttag(self, tag, attrs):

        if tag == "a":
            for key, value in attrs:
                if key == "href" and value.startswith("/photo/"):
                    page = "http://www.imagefap.com{}".format(value)
                    if page not in self.photo_pages:
                        self.photo_pages.append(page)

    def reset(self):
        self.photo_pages = []
        HTMLParser.reset(self)


class ImageLinkScraper(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        # Keep track of full image links grabbed
        self.image_links = []

    def handle_starttag(self, tag, attrs):

        if tag == "a":
            for key, value in attrs:
                if key == "href" and \
                        value.startswith("http://fap.to/images/full"):
                    if value not in self.image_links:
                        self.image_links.append(value)

    # In case we need to call the reset method (which scraps all of the data
    # in the parent). This also resets the image_links attribute.
    def reset(self):
        self.image_links = []
        HTMLParser.reset(self)


class ImageDownloader(threading.Thread):

    def __init__(self, semaphore, url, prefix, directory):
        self.semaphore = semaphore
        self.url = url
        self.prefix = prefix
        self.directory = directory
        self.id = hash(self)

        self.file_name = os.path.join(directory, "{}{}{}".format(prefix, "-", url.split("/")[-1]))

        threading.Thread.__init__(self)

    def run(self):

        self.semaphore.acquire()
        response = requests.get(self.url, stream=True)
        self.semaphore.release()

        if response.status_code != 200:
            warn("Thread {}: Trying to grab image at '{}', got status code of {}".format(
                self.id, self.url, response.status_code))
        else:
            with open(self.file_name, "wb") as f:
                shutil.copyfileobj(response.raw, f)

if __name__ == "__main__":
    main()
