from . import press_lang
from . import utils
from .ast import press_lang as ast


def parse(text):
    return press_lang.parse(text, actions=ast.Actions)


def test_numbers():
    e = parse('123')
    assert e.elements[1].expr.value == "123"


def test_strings():
    e = parse('"123"')
    assert e.elements[1].expr.value == '"123"'


def test_functions():
    e = parse('function(){}')
    assert e.elements[1].expr.text == 'function(){}'
    e = parse('function(a){}')
    assert e.elements[1].expr.elements[3].name == 'a'


def test_calls():
    e = parse('call()')
    assert e.elements[1].expr.name == 'call'
    e = parse('call(1)')
    assert e.elements[1].expr.name == 'call'
    e = parse('call(1, 2, 3)')
    assert e.elements[1].expr.name == 'call'
    e = parse('call 1')
    assert e.elements[1].expr.name == 'call'
    e = parse('call')
    assert e.elements[1].expr.name == 'call'
    e = parse('call ')
    assert e.elements[1].expr.name == 'call'


def test_exprs():
    e = parse('1;2;3')
    assert e.elements[1].expr.value == '1'
    assert e.elements[1].exprs.elements[0].expr.value == '2'
    assert e.elements[1].exprs.elements[1].expr.value == '3'


def test_comments():
    e = parse('1// blah')
    assert e.elements[1].expr.value == '1'
    e = parse('1/* alalal */')
    assert e.elements[1].expr.value == '1'


def test_actions():
    e = parse('1')
    assert isinstance(e.elements[1].expr, ast.Number)
    e = parse('"1"')
    assert isinstance(e.elements[1].expr, ast.String)
    e = parse('true')
    assert e.elements[1].expr is True
    e = parse('false')
    assert e.elements[1].expr is False
    e = parse('null')
    assert e.elements[1].expr is None
