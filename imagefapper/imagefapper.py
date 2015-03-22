"""
Usage:  imagefapper  [--dir=<directory>] [--num_threads=<num_threads>] <gallery_url>
        imagefapper --version
        imagefapper --help


        --dir, -d           The directory (under .) to which the images will be loaded.
                                This directory will be created if it doesn't exist. If not
                                specified, the directory is based off of the gallery name.
        --num_threads, -n   The number of threads to use [default: 10].

"""
import click
import os
import re
import requests
import six

from six.moves import urllib_parse
from ._version import __version__

from .scraper import AttributeScraper
from .image import Grabber


@click.command()
@click.option("--directory", type=str, default=None, help="Specify a directory (in .) to store images (if not specified, the directory name is based off of the gallery name)")
@click.option("--num_threads", type=int, default=10, help="The number of threads to use [default: 10]")
@click.argument("url")
@click.version_option(version=__version__)
def main(directory, num_threads, url):
    """Download the imagefap.com gallery from URL."""
    gallery = Gallery(url=url, directory=directory, num_threads=num_threads)

    gallery.download()


class ScraperException(Exception):
    pass


class Gallery(object):

    def __init__(self, url, num_threads=10, directory=None):
        self.url = url

        if not isinstance(num_threads, six.integer_types) or num_threads <= 0:
            raise ValueError("num_threads must be a positive integer")

        self.num_threads = num_threads

        self.id = url.split("/")[-2]

        assert re.match("^\d+$", self.id), "Unexpected gallery id: {}".format(self.id)

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

        self.directory = directory or os.path.join(".", self.name.replace(" ", "_").lower())

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

        scraper = AttributeScraper("a", "href", "^/photo/")
        scraper.scrape(html)

        self.photo_pages = ["http://www.imagefap.com{}".format(x) for x in scraper.values]

    def get_image_links(self):
        # TODO: Make this threaded as well, since it's a bottleneck.
        if not self.photo_pages:
            self.get_photo_pages()

        photo_page = self.photo_pages[0]

        response = requests.get(photo_page)

        if response.status_code != 200:
            raise ScraperException(
                "For url '{}', received status code {}".format(self.full_page_url, response.status_code))

        html = response.text

        scraper = AttributeScraper("a", "href", "^http://fap.to/images/full")
        scraper.scrape(html)

        for link in scraper.values:
            if link not in self.image_links:
                self.image_links.append(link)

    def download(self):

        if not self.image_links:
            self.get_image_links()

        grabber = Grabber(self.image_links, self.directory, num_threads=self.num_threads)
        grabber.grab()


if __name__ == "__main__":
    main()
