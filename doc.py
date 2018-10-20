from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
import reportlab.lib.pagesizes
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from runtime import Runtime
from parsers import press_lang, template
from parsers.ast import press_lang as press_lang_ast
from parsers.ast import template as template_ast


class Document:
    def __init__(self, fname):
        self.font = 'Tahoma'
        self.font_size = 12
        self.page_size_name = 'A4'
        self.margins = [2 * cm, 3 * cm]
        self.leading = 1.0
        self.page_size = getattr(reportlab.lib.pagesizes, self.page_size_name)

        self.canvas = None

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
        self.intro_code.execute(self, None)

    def parse(self, text):
        return template.parse(text.strip(), actions=template_ast.Actions)

    def transform(self, ast):
        print(ast.elements)
        return ast.elements

    def set_text_origin(self, text):
        text.setTextOrigin(
            self.margins[0],
            self.page_size[1] - self.margins[1] - text._fontsize
        )

    def render(self, text):
        items = self.transform(self.parse(text))
        self.canvas.rect(
            self.margins[0],
            self.margins[1],
            self.page_size[0] - 2 * self.margins[0],
            self.page_size[1] - 2 * self.margins[1]
        )

        text = self.canvas.beginText()
        first_line = True
        for item in items:
            if type(item) == str:
                if first_line:
                    self.set_text_origin(text)
                    first_line = False
                text.textLine(item)

                if text.getY() < self.margins[1]:
                    self.canvas.drawText(text)
                    self.canvas.showPage()
                    self.canvas.setFont(
                        self.font,
                        self.font_size,
                        self.font_size * self.leading
                    )
                    text = self.canvas.beginText()
                    first_line = True
            if isinstance(item, press_lang_ast.Statements):
                item.execute(self, text)

        if text:
            self.canvas.drawText(text)

    def save(self):
        self.canvas.save()
