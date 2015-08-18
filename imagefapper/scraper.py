import re
import six.moves as sm

__all__ = ["AttributeScraper"]


class AttributeScraper(sm.html_parser.HTMLParser):
    """
    A scraper specifically built for grabbing the value of a
    given attribute residing within a given type of tag,
    provided that the value matches a given regex pattern.
    """

    def __init__(self, tag, attribute, pattern):
        """

        :param str tag: The name of the tag to capture (eg ``"a"``, ``"img"``, etc)
        :param str attribute: The name of the tag within the attribute to grab
        (eg ``"href"``, ``"src"``, etc)
        :param str pattern: A string representing a regular expression pattern.
         Only values matching this pattern are taken.
        """
        super(AttributeScraper, self).__init__()
        self.tag = tag
        self.attribute = attribute
        self.pattern = pattern
        self.values = []  #: Matching values are stored as a list in the ``values`` attribute

    def handle_starttag(self, tag, attrs):

        if tag == self.tag:
            for key, value in attrs:
                if key == self.attribute and re.match(self.pattern, value):
                    self.values.append(value)

    def scrape(self, data):

        self.values = []
        self.reset()
        self.feed(data)
