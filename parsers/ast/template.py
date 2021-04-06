
from .press_lang import Actions as Base, Node


class Template(Node):
    def __init__(self, parts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elements = parts
        self.lazy = True

    def execute(self, runtime, caller: Node = None):
        self.caller = caller

        runtime.push_buffer()
        if not self.elements[0]:
            self.elements = self.elements[1:]
        for element in self.elements:
            if type(element) == str and element:
                runtime.add_text(element)
            else:
                element.execute(runtime, caller=self)
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
        return Template(parts, start=start, end=end)
