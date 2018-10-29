from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
import reportlab.lib.pagesizes
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from runtime import Runtime, TextLine
from parsers import press_lang, template
from parsers.ast import press_lang as press_lang_ast
from parsers.ast import template as template_ast


class Document:
    def __init__(self, fname):
        self.font = 'Tahoma'
        self.font_size = 12
        self.page_size_name = 'A4'
        self.margins = [1.5 * cm, 2 * cm]
        self.leading = 1.0
        self.page_size = getattr(reportlab.lib.pagesizes, self.page_size_name)

        self.canvas = None
        self.runtime = None
        self.intro = None
        self.intro_code = None

        self.init_canvas(fname)

    def init_canvas(self, fname):
        self.canvas = Canvas(
            '{}.pdf'.format(fname),
            pagesize=self.page_size
        )
        pdfmetrics.registerFont(TTFont(self.font, '{}.ttf'.format(self.font)))
        self.canvas.setFont(
            self.font,
            self.font_size,
            self.font_size * self.leading
        )

    def init(self, intro):
        self.runtime = Runtime()
        self.intro = intro.strip()
        self.intro_code = press_lang.parse(
            self.intro,
            actions=press_lang_ast.Actions
        )
        self.intro_code.execute(self.runtime)

    def parse(self, text):
        return template.parse(text.strip(), actions=template_ast.Actions)

    def render(self, text):
        items = self.parse(text).execute(self.runtime)
        print(items)

        self.canvas.rect(
            self.margins[0],
            self.margins[1],
            self.page_size[0] - 2 * self.margins[0],
            self.page_size[1] - 2 * self.margins[1]
        )

        txt = self.canvas.beginText()
        first_line = True
        for item in items:
            item.apply(txt)
            if first_line:
                item.set_text_origin(txt)
                first_line = False
            if isinstance(item, TextLine):
                txt.textLine(item.text)
            else:
                if item.text.endswith('\n'):
                    txt.textLine(item.text[:-1])
                else:
                    txt.textOut(item.text)

            if txt.getY() < self.margins[1]:
                self.canvas.drawText(txt)
                self.canvas.showPage()
                self.canvas.setFont(
                    self.font,
                    self.font_size,
                    self.font_size * self.leading
                )
                txt = self.canvas.beginText()
                first_line = True

        if txt:
            self.canvas.drawText(txt)

    def save(self):
        self.canvas.save()
