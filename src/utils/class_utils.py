import json
from html.parser import HTMLParser


class RegionCodes:
    def __init__(self):
        with open('static/regioncodes.json') as f:
            self.regioncodes = json.loads(f.read())

    def get(self, item: str) -> str:
        return self.regioncodes.get(item.upper())


# noinspection SpellCheckingInspection
class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)
