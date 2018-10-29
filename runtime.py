from copy import copy

import reportlab.lib.pagesizes
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.textobject import PDFTextObject


def size(runtime, size):
    runtime.state.set_font_size(size)


def font(runtime, fontname, fontsize, leading=None):
    if fontname not in pdfmetrics._fonts:
        try:
            pdfmetrics.registerFont(TTFont(fontname, '{}.ttf'.format(fontname)))
        except:
            pdfmetrics.registerFont(TTFont(fontname, '{}.ttc'.format(fontname)))

    if leading is not None:
        leading = float(leading)
    runtime.state.set_font(fontname, fontsize, leading)


def indent(runtime, length):
    runtime.state.set_indent(length)


def set_state(runtime, el):
    runtime.state = el


def get_state(runtime):
    return copy(runtime.state)


def output(runtime, el):
    if type(el) == list:
        for item in el:
            runtime.items[-1].append(item)
    else:
        runtime.add_text(el)


def line(runtime, el):
    if type(el) == list:
        if len(el) > 1:
            raise ValueError('More than 1 element for `line` call is ambiguous, use `output`')
        for item in el:
            if not isinstance(item, TextLine):
                item = TextLine(item.text, item.state)
            runtime.items[-1].append(item)
    else:
        runtime.add_line(el)


def get(runtime, el):
    return runtime.get(el)


class State:
    DEFAULT_LEADING = 1.0

    def __init__(self):
        self.font = 'Tahoma'
        self.font_size = 12
        self.page_size_name = 'A4'
        self.margins = [1.5 * cm, 2 * cm]
        self.leading = self.DEFAULT_LEADING
        self.page_size = getattr(reportlab.lib.pagesizes, self.page_size_name)
        self.indent = 0

    def set_font(self, font, size, leading=None):
        self.font = font
        self.font_size = size
        if leading:
            self.leading = leading

    def set_font_size(self, size):
        self.font_size = size
        self.leading = self.DEFAULT_LEADING

    def set_indent(self, indent):
        self.indent = indent


class TextFragment:
    def __init__(self, text, state):
        self.text = text
        self.state = state

    def __repr__(self):
        return '<{}: {}; {} {}; in {}>'.format(
            self.__class__.__name__,
            repr(self.text[:10]),
            self.state.font,
            self.state.font_size,
            self.state.indent,
        )

    def apply(self, text: PDFTextObject):
        state = self.state
        text.setFont(state.font, state.font_size, state.font_size * state.leading)
        indent = state.indent - getattr(text, '_indent', 0)
        text._indent = state.indent
        text.setXPos(indent)

    def set_text_origin(self, text: PDFTextObject):
        text.setTextOrigin(
            self.state.margins[0],
            self.state.page_size[1] - self.state.margins[1] - self.state.font_size
        )


class TextLine(TextFragment):
    def __init__(self, text, state):
        super().__init__(text, state)


class Runtime:
    def __init__(self):
        self.stack = [{}]
        self.load_builtin()
        self.state = State()
        self.items = []
        self.newlines_active = True

    def load_builtin(self):
        self.set('size', size)
        self.set('font', font)
        self.set('indent', indent)
        self.set('output', output)
        self.set('line', line)
        self.set('set_state', set_state)
        self.set('get_state', get_state)
        self.set('get', get)

    def add_text(self, text):
        if self.newlines_active:
            if text and text[-1] == '\n':
                text = text[:-1]
            for line in text.split('\n'):
                self.items[-1].append(TextLine(line, copy(self.state)))

    def add_line(self, text):
        self.items[-1].append(TextLine(text, copy(self.state)))

    def push_buffer(self):
        self.items.append([])

    def pop_buffer(self):
        return self.items.pop()

    def get(self, key):
        for d in reversed(self.stack):
            if key in d:
                return d[key]
        raise KeyError(key)

    def set(self, key, value):
        self.stack[-1][key] = value

    def push(self):
        self.stack.append({})

    def pop(self):
        self.stack.pop()

    def has(self, key):
        for d in self.stack:
            if key in d:
                return True
        return False
