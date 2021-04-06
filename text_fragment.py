import reportlab.lib
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth as text_width
from reportlab.pdfgen.textobject import PDFTextObject


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
        return '<{}: {}; {} {}; col {}/{} m {}>'.format(
            self.__class__.__name__,
            repr(self.text[:10]),
            self.state.font,
            self.state.font_size,
            self.state.column,
            len(self.state.columns),
            self.state.margin
        )

    @property
    def width(self):
        return self.state.widths[self.state.column - 1]

    def apply(self, text: PDFTextObject, runtime=None, text_only=False):
        state = self.state
        if not text_only:
            if len(state.columns) > 0:
                if runtime.column_state is None:
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

                if state.columns_reset:
                    prev_x  = runtime.column_state.get('prev_x', 0)
                    runtime._reset_columns()
                    prev_y = 0

                for col in range(len(state.columns)):
                    if col + 1 < state.column:
                        my_x += state.widths[col] + state.column_gap
                if not self.text.startswith(' for predicting cell types in Mouse Cell Atlas'):
                    print("Moving column {} {}; {}".format(my_x - prev_x, -prev_y, repr(self.text)))
                    text.moveCursor(my_x - prev_x, -prev_y)
                runtime.column_state['previous'] = state.column
                runtime.column_state['prev_x'] = my_x
                runtime.column_state[state.column] = (len(self.lines())) * state.font_size * state.leading
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
                # print((width, used_width, wwidth, repr(word)))
                if not used_width or used_width + wwidth < width:
                    line_words.append(word)
                    used_width += wwidth + space_width
                else:
                    result.append(' '.join(line_words))
                    line_words = [word]
                    used_width = wwidth
            if line_words:
                result.append(' '.join(line_words))
        if not result and len(self.text) > 0:
            result.append('')
        return result

    def text_line(self, text: PDFTextObject, line, final=False):
        state = self.state
        if len(state.columns) > 1 \
                and 'align' in state.columns[state.column - 1] \
                and state.columns[state.column - 1]['align'] == 'right':
            text.setXPos(state.widths[state.column - 1] - self.text_width(line))
            # print(state.widths[state.column - 1] - self.text_width(line))
        if final and not isinstance(self, TextLine):
            text.textOut(line)
        else:
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
