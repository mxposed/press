from copy import copy

from reportlab.lib.fonts import tt2ps, addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from parsers.ast.press_lang import prepare_arg
from runtime import Runtime, register, PythonCall
from text_fragment import TextLine


def reportlab_mapping(font: TTFont):
    family_name = font.face.familyName.decode('utf-8')
    full_name = font.face.name.decode('utf-8')
    style_name = font.face.styleName.decode('utf-8').lower()
    bold = int('bold' in style_name)
    italic = int('italic' in style_name)
    addMapping(family_name, bold, italic, full_name)


@register
def size(runtime: Runtime, size, leading=None):
    runtime.state.set_font_size(size, leading)


@register
def font(runtime, fontname, fontsize, leading=None):
    if fontname not in pdfmetrics._fonts and not fontname in pdfmetrics.standardFonts:
        try:
            font = TTFont(fontname, '{}.ttf'.format(fontname))
        except:
            font = TTFont(fontname, '{}.ttc'.format(fontname))
        pdfmetrics.registerFont(font)
        reportlab_mapping(font)
        if font.face.fileKind == 'TTC':
            for idx, _ in enumerate(font.face.subfontOffsets[1:]):
                tt_font = TTFont(fontname, '{}.ttc'.format(fontname), subfontIndex=idx + 1)
                tt_font.fontName = tt_font.face.name.decode('utf-8')
                pdfmetrics.registerFont(tt_font)
                reportlab_mapping(tt_font)

    if leading is not None:
        leading = float(leading)
    runtime.state.set_font(fontname, fontsize, leading)


@register
def indent(runtime, length):
    runtime.state.set_indent(length)


@register
def set_state(runtime, el):
    runtime.state = el


@register
def get_state(runtime):
    return copy(runtime.state)


@register
def output(runtime, el):
    if type(el) == list:
        for item in el:
            runtime.items[-1].append(item)
    else:
        runtime.add_text(el)


@register
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


@register
def get(runtime, el):
    return runtime.get(el)


@register
def margin(runtime, el):
    runtime.state.set_margin(el)


@register
def columns(runtime, specs):
    runtime.state.set_columns(specs)


@register
def column(runtime, column):
    if len(runtime.state.columns) < column:
        raise ValueError(
            'Column {} not defined by previous call to `columns`'.format(column)
        )
    runtime.state.set_column(column)


@register
def i(runtime, el, caller=None):
    fontname = runtime.state.font
    italic = tt2ps(fontname, 0, 1)
    runtime.state.font = italic
    output(runtime, prepare_arg(PythonCall(caller), runtime, el))
    runtime.state.font = fontname


@register
def tt(runtime, el, caller=None):
    fontname = runtime.state.font
    font(runtime, 'Courier', runtime.state.font_size, runtime.state.leading)
    output(runtime, prepare_arg(PythonCall(caller), runtime, el))
    runtime.state.font = fontname
