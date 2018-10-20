
from .press_lang import Actions as Base


class Template:
    def __init__(self, parts):
        self.elements = parts


class Actions(Base):
    @staticmethod
    def make_text(input, start, end, elements):
        return input[start:end]

    @staticmethod
    def make_template(input, start, end, elements):
        parts = []
        parts.append(elements[0].text)
        if elements[1].elements:
            for el in elements[1].elements:
                parts.append(el.insertion.statements)
                if el.elements[1].text:
                    parts.append(el.elements[1].text)
        return Template(parts)
