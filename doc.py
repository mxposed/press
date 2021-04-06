import os

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
    def __init__(self, file):
        self.file = file

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

        self.init_canvas(file)

    def init_canvas(self, fname):
        fname = os.path.splitext(fname)[0]
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
        self.canvas.setCreator("press")
        self.canvas.setProducer("")
        self.canvas.setAuthor("")
        self.canvas.setTitle("")
        self.canvas.setSubject("")

    def init(self, intro):
        self.runtime = Runtime()
        self.intro = intro.strip()
        self.intro_code = press_lang.parse(
            self.intro,
            actions=press_lang_ast.Actions
        )
        self.intro_code.file = os.path.abspath(self.file)
        self.intro_code.text = self.intro
        self.intro_code.set_parent(None)
        self.intro_code.execute(self.runtime)

    def parse(self, text):
        root = template.parse(text.strip(), actions=template_ast.Actions)
        root.prefix = self.intro + '\n--------\n'
        root.file = os.path.abspath(self.file)
        root.text = text.strip()
        root.set_parent(None)
        return root

    def render(self, text):
        items = self.parse(text).execute(self.runtime)
        print(items)

        txt = self.canvas.beginText()
        first_line = True
        for item in items:
            item.apply(txt, runtime=self.runtime)

            lines = item.lines()
            for idx, line in enumerate(lines):
                if first_line:
                    item.set_text_origin(txt)
                first_line = False
                # print(repr((line, idx)))
                item.text_line(txt, line, final=idx == len(lines) - 1)

                if txt.getY() < self.margins[1]:
                    self.canvas.drawText(txt)
                    self.canvas.showPage()
                    self.canvas.setFont(
                        self.font,
                        self.font_size,
                        self.font_size * self.leading
                    )
                    txt = self.canvas.beginText()
                    item.apply(txt, text_only=True, runtime=self.runtime)
                    first_line = True

        if txt:
            self.canvas.drawText(txt)

    def save(self):
        self.canvas.save()
