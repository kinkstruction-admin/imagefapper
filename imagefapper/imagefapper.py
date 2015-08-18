import click
import os
import re
import requests
import six

import six.moves
from ._version import __version__

from . import scraper as scr

from .image import Grabber


@click.command()
@click.option("--directory", type=str, default=None,
              help="Specify a directory (in .) to store images (if not specified, the directory name is based off of the gallery name)")
@click.option("--num_threads", type=int, default=10, help="The number of threads to use [default: 10]")
@click.argument("url")
@click.version_option(version=__version__)
def main(directory, num_threads, url):
    """Download the imagefap.com gallery from URL."""
    gallery = Gallery(url=url, directory=directory, num_threads=num_threads)

    gallery.download()


class ScraperError(Exception):
    pass


class Gallery(object):
    """
    This class is responsible for grabbing the URLs of all of the stored images
    in the gallery and passing them on to an ``image.Grabber`` object
    for threaded downloading.
    """

    def __init__(self, url, num_threads=10, directory=None):
        """
        :param str url: The URL of the main page of the gallery.
        :param int num_threads: The number of threads to use.
        :param str directory: The directory (within ``.``) where the gallery folder
        will be placed.
        """
        self.url = url

        if not isinstance(num_threads, six.integer_types) or num_threads <= 0:
            raise ValueError("num_threads must be a positive integer")

        self.num_threads = num_threads

        self.id = url.split("/")[-2]  #: The gallery ID (from the URL) is stored in the ``id`` attribute.

        assert re.match("^\d+$", self.id), "Unexpected gallery id: {}".format(self.id)

        parsed = six.moves.urllib_parse.urlparse(url)

        self.base_url = url  #: The base URL of the gallery is stored in the ``base_url`` attribute.
        self.full_page_url = url  #: The full page gallery of the URL is stored in the ``full_page_url`` attribute.

        self.photo_pages = []  #: The ``photo_pages`` attribute is filled by the ``get_photo_pages`` method.
        self.image_links = []  #: The ``image_links`` attribute is filled by the ``get_image_links`` method.

        if parsed.query:
            query_parts = dict(six.moves.urllib_parse.parse_qsl(parsed.query))  # query k-v pairs
            self.base_url = re.sub(
                "\?$", "", parsed.geturl().replace(parsed.query, ""))  # get rid of query to get base_url.

            # Hacky check to see if we're in the "Detailed View" or "One page" view of the gallery.
            # If we have "gid=xxxxxxx" in the URL, then the value of "gid" is the same as the gallery ID.
            if "gid" in query_parts:
                assert query_parts.get("gid") == self.id, \
                    "gid from URL and gid from query don't match ({},{})".format(self.id, query_parts.get("gid"))

        self.full_page_url = "{}?gid={}&view=2".format(self.base_url, self.id)

        self.name = self.base_url.split("/")[-1].replace("-", " ")

        self.directory = directory or os.path.join(".", self.name.replace(" ", "_").lower())
        self.directory = re.sub("\.+$", "", self.directory)

        if not os.path.exists(self.directory):
            os.mkdir(self.directory)
        elif not os.path.isdir(self.directory):
            raise ValueError("The file '{}' exists and is not a directory".format(self.directory))

    def get_photo_pages(self):
        """
        Takes the ``full_page_url`` attribute (pointing to the URL of the gallery page containing
        links to all of the images, not the paginated view), and parses out the links to each
        individual full-sized image. This method populates the ``photo_pages`` attribute.
        """

        response = requests.get(self.full_page_url)

        if response.status_code != 200:
            raise ScraperError(
                "For url '{}', received status code {}".format(self.full_page_url, response.status_code))

        html = response.text

        scraper = scr.AttributeScraper("a", "href", "^/photo/")
        scraper.scrape(html)

        self.photo_pages = ["http://www.imagefap.com{}".format(x) for x in scraper.values]

        print("Got {} photo pages".format(len(self.photo_pages)))

    def get_image_links(self):
        """
        Takes the URLs from the ``photo_pages`` attribute and grabs the links to the full-sized
        images therein. This method modifies the ``image_links`` attribute.
        """
        # TODO: Make this threaded as well, since it's a bottleneck.
        if not self.photo_pages:
            self.get_photo_pages()

        for photo_page in self.photo_pages:

            response = requests.get(photo_page)

            if response.status_code != 200:
                raise ScraperError(
                    "For url '{}', received status code {}".format(self.full_page_url, response.status_code))

            html = response.text

            scraper = scr.AttributeScraper("img", "src", "^http://x.imagefapusercontent.com/")
            scraper.scrape(html)

            for link in scraper.values:
                if link not in self.image_links:
                    self.image_links.append(link)


        print("Got {} image links".format(len(self.image_links)))

    def download(self):

        if not self.image_links:
            self.get_image_links()

        grabber = Grabber(self.image_links, self.directory, num_threads=self.num_threads)
        grabber.grab()


if __name__ == "__main__":
    main()
