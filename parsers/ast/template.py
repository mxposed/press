
from .press_lang import Actions as Base


class Template:
    def __init__(self, parts):
        self.elements = parts
        self.lazy = True

    def execute(self, runtime):
        runtime.push_buffer()
        if not self.elements[0]:
            self.elements = self.elements[1:]
        for element in self.elements:
            if type(element) == str:
                if element[0] == '\n':
                    if element[1:]:
                        runtime.add_text(element[1:])
                elif element:
                    runtime.add_text(element)
            else:
                element.execute(runtime)
        return runtime.pop_buffer()


class Actions(Base):
    @staticmethod
    def make_text(input, start, end, elements):
        return input[start:end]

    @staticmethod
    def make_template(input, start, end, elements):
        parts = [elements[0].text]
        if elements[1].elements:
            for el in elements[1].elements:
                parts.append(el.insertion.statements)
                if el.elements[1].text:
                    parts.append(el.elements[1].text)
        return Template(parts)
