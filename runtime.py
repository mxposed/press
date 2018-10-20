from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def size(doc, text, size):
    text.setFont(text._fontname, int(size.value))


def font(doc, text, fontname, fontsize):
    fontname = eval(fontname.value)
    if fontname not in pdfmetrics._fonts:
        try:
            pdfmetrics.registerFont(TTFont(fontname, '{}.ttf'.format(fontname)))
        except:
            pdfmetrics.registerFont(TTFont(fontname, '{}.ttc'.format(fontname)))

    text.setFont(fontname, int(fontsize.value))


def indent(doc, text, length):
    text.setXPos(int(length.value))


def output(doc, text, el):
    text.textLine(doc.runtime.defs[el.subject].elements[0])


def set_state(doc, text, el):
    text.setFont('Tahoma', 12)
    text.setXPos(-20)


class Runtime:
    def __init__(self):
        self.defs = {}
        self.load_builtin()

    def load_builtin(self):
        self.defs['size'] = size
        self.defs['font'] = font
        self.defs['indent'] = indent
        self.defs['output'] = output
        self.defs['set_state'] = set_state
