from . import template
from . import utils
from .ast import template as ast


def parse(text):
    return template.parse(text, actions=ast.Actions)


def test_template():
    e = parse('123')
    assert e.elements[0] == '123'
    e = parse('123[]')
    assert e.elements[0] == '123'
    assert len(e.elements) == 2
    assert len(e.elements[1].elements) == 0


def test_calls():
    e = parse('123[blah]')
    utils.inspect(e)
    assert e.elements[1].elements[0].subject == 'blah'
    e = parse('123[][blah]')
    assert e.elements[2].elements[0].subject == 'blah'
    e = parse('123[blah[a1][a2]]')
    call = e.elements[1].elements[0]
    assert call.subject == 'blah'
    assert call.args[0].elements[0] == 'a1'
    assert call.args[1].elements[0] == 'a2'
    e = parse('123[blah[text[Z]text]]')
    call = e.elements[1].elements[0]
    assert call.subject == 'blah'
    inner_call = call.args[0].elements[1].elements[0]
    assert inner_call.subject == 'Z'
