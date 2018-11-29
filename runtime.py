from collections import defaultdict
from copy import copy

import reportlab.lib.pagesizes
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.textobject import PDFTextObject
from reportlab.pdfbase.pdfmetrics import stringWidth as text_width


class Runtime:
    def __init__(self):
        self.stack = [{}]
        self.load_builtin()
        self.state = State()
        self.items = []
        self.newlines_active = True
        self.column_state = None

    def load_builtin(self):
        self.set('size', size)
        self.set('font', font)
        self.set('indent', indent)
        self.set('output', output)
        self.set('line', line)
        self.set('set_state', set_state)
        self.set('get_state', get_state)
        self.set('get', get)
        self.set('margin', margin)
        self.set('columns', columns)
        self.set('column', column)

    def add_text(self, text):
        if self.newlines_active:
            if text and text[-1] == '\n':
                text = text[:-1]
            self.items[-1].append(TextFragment(text, copy(self.state)))
            self.state.reset()

    def add_line(self, text):
        self.items[-1].append(TextLine(text, copy(self.state)))
        self.state.reset()

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

    def _reset_columns(self):
        self.column_state = defaultdict(int)
        self.column_state['previous'] = None


class State:
    DEFAULT_LEADING = 1.0
    DEFAULT_COLUMN_GAP = 10

    def __init__(self):
        self.font = 'Tahoma'
        self.font_size = 12
        self.page_size_name = 'A4'
        self.margins = [1.5 * cm, 2 * cm]
        self.leading = self.DEFAULT_LEADING
        self.page_size = getattr(reportlab.lib.pagesizes, self.page_size_name)
        self.indent = 0
        self.margin = 0

        self.column_gap = self.DEFAULT_COLUMN_GAP
        self.columns_reset = False
        self.columns = []
        self.column = 1

        self.calculate_widths()

    def reset(self):
        self.margin = 0
        self.columns_reset = False

    def set_font(self, font, size, leading=None):
        self.font = font
        self.font_size = size
        if leading:
            self.leading = leading

    def set_font_size(self, size, leading=None):
        self.font_size = size
        if leading is None:
            leading = self.DEFAULT_LEADING
        self.leading = leading

    def set_indent(self, indent):
        self.indent = indent

    def set_margin(self, margin):
        self.margin = margin

    def set_columns(self, specs):
        self.columns_reset = True
        self.columns = specs
        self.calculate_widths()

    def set_column(self, column):
        self.column = column

    def calculate_widths(self):
        page_width = self.page_size[0] - 2 * self.margins[0]
        if not self.columns or len(self.columns) == 1:
            self.widths = {0: page_width}
            return
        remaining_width = page_width - self.column_gap * (len(self.columns) - 1)
        unspec_cols = 0
        widths = {}
        for col, spec in enumerate(self.columns):
            if 'width' in spec and type(spec['width']) == int:
                widths[col] = spec['width']
                remaining_width -= widths[col]
            else:
                unspec_cols += 1

        for col, _ in enumerate(self.columns):
            if col not in widths:
                widths[col] = remaining_width / unspec_cols
        self.widths = widths


class TextFragment:
    def __init__(self, text, state):
        self.text = text
        self.state = state

    def __repr__(self):
        return '<{}: {}; {} {}; col {}/{} r {}>'.format(
            self.__class__.__name__,
            repr(self.text[:10]),
            self.state.font,
            self.state.font_size,
            self.state.column,
            len(self.state.columns),
            self.state.columns_reset
        )

    @property
    def width(self):
        return self.state.widths[self.state.column - 1]

    def apply(self, text: PDFTextObject, runtime: Runtime = None, text_only=False):
        state = self.state
        if not text_only:
            if len(state.columns) > 1:
                if state.columns_reset:
                    runtime._reset_columns()

                prev_col = runtime.column_state['previous']
                prev_y = 0
                if prev_col and prev_col != state.column:
                    prev_y = runtime.column_state[prev_col]
                prev_x = 0
                my_x = 0
                if prev_col:
                    for col in range(len(state.columns)):
                        if col + 1 < prev_col:
                            prev_x += state.widths[col] + state.column_gap

                for col in range(len(state.columns)):
                    if col + 1 < state.column:
                        my_x += state.widths[col] + state.column_gap
                text.moveCursor(my_x - prev_x, -prev_y)
                runtime.column_state['previous'] = state.column
                runtime.column_state[state.column] = len(self.lines()) * state.font_size * state.leading
            if state.margin:
                text.moveCursor(0, state.margin)

        text.setFont(state.font, state.font_size, state.font_size * state.leading)
        indent = state.indent - getattr(text, '_indent', 0)
        text._indent = state.indent
        text.setXPos(indent)

    def set_text_origin(self, text: PDFTextObject):
        text.setTextOrigin(
            self.state.margins[0],
            self.state.page_size[1] - self.state.margins[1] - self.state.font_size
        )

    def text_width(self, text):
        return text_width(text, self.state.font, self.state.font_size)

    def lines(self):
        width = self.width
        space_width = self.text_width(' ')
        result = []
        for line in self.text.split('\n'):
            line_words = []
            used_width = 0
            for word in line.split(' '):
                wwidth = self.text_width(word)
                if not used_width or used_width + wwidth < width:
                    line_words.append(word)
                    used_width += wwidth + space_width
                else:
                    result.append(' '.join(line_words))
                    line_words = [word]
                    used_width = 0
            if line_words:
                result.append(' '.join(line_words))
        return result

    def text_line(self, text: PDFTextObject, line):
        state = self.state
        if len(state.columns) > 1 \
                and 'align' in state.columns[state.column - 1] \
                and state.columns[state.column - 1]['align'] == 'right':
            text.setXPos(state.widths[state.column - 1] - self.text_width(line))
            print(state.widths[state.column - 1] - self.text_width(line))
        text.textLine(line)
        if len(state.columns) > 1 \
                and 'align' in state.columns[state.column - 1] \
                and state.columns[state.column - 1]['align'] == 'right':
            text.setXPos(-state.widths[state.column - 1] + self.text_width(line))

        # if isinstance(item, TextLine):
        #     txt.textLine(item.text)
        # else:
        #     if item.text.endswith('\n'):
        #         txt.textLine(item.text[:-1])
        #     else:
        #         txt.textOut(item.text)


class TextLine(TextFragment):
    def __init__(self, text, state):
        super().__init__(text, state)

    def lines(self):
        return [self.text]


def size(runtime: Runtime, size, leading=None):
    runtime.state.set_font_size(size, leading)


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


def margin(runtime, el):
    runtime.state.set_margin(el)


def columns(runtime, specs):
    runtime.state.set_columns(specs)


def column(runtime, column):
    if len(runtime.state.columns) < column:
        raise ValueError(
            'Column {} not defined by previous call to `columns`'.format(column)
        )
    runtime.state.set_column(column)
