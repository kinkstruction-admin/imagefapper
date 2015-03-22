import re

from html.parser import HTMLParser


class AttributeScraper(HTMLParser):

    def __init__(self, tag, attribute, pattern):
        HTMLParser.__init__(self)
        self.tag = tag
        self.attribute = attribute
        self.pattern = pattern
        self.values = []

    def handle_starttag(self, tag, attrs):

        if tag == self.tag:
            for key, value in attrs:
                if key == self.attribute and re.match(self.pattern, value):
                    self.values.append(value)

    def scrape(self, data):

        self.values = []
        self.reset()
        self.feed(data)
