from . import press_lang
from . import utils
from .ast import press_lang as ast


def parse(text):
    return press_lang.parse(text, actions=ast.Actions)


def test_numbers():
    e = parse('123')
    assert e.elements[0].value == '123'


def test_strings():
    e = parse('"123"')
    assert e.elements[0].value == '"123"'


def test_functions():
    e = parse('function(){}')
    assert len(e.elements[0].args) == 0
    assert len(e.elements[0].code.elements) == 0
    e = parse('function(a){}')
    assert e.elements[0].args[0] == 'a'


def test_calls():
    e = parse('call()')
    assert e.elements[0].subject == 'call'
    e = parse('call(1)')
    assert e.elements[0].subject == 'call'
    assert e.elements[0].args[0].value == '1'
    e = parse('call(1, 2, 3)')
    assert e.elements[0].subject == 'call'
    assert e.elements[0].args[0].value == '1'
    assert e.elements[0].args[1].value == '2'
    assert e.elements[0].args[2].value == '3'
    e = parse('call 1')
    assert e.elements[0].subject == 'call'
    assert e.elements[0].args[0].value == '1'
    e = parse('call')
    assert e.elements[0].subject == 'call'
    e = parse('call ')
    assert e.elements[0].subject == 'call'


def test_exprs():
    e = parse('1;2;3')
    assert e.elements[0].value == '1'
    assert e.elements[1].value == '2'
    assert e.elements[2].value == '3'


def test_comments():
    e = parse('1// blah')
    assert e.elements[0].value == '1'
    e = parse('1/* alalal */')
    assert e.elements[0].value == '1'


def test_values():
    e = parse('1')
    assert isinstance(e.elements[0], ast.Number)
    e = parse('"1"')
    assert isinstance(e.elements[0], ast.String)
    e = parse('true')
    assert e.elements[0] is True
    e = parse('false')
    assert e.elements[0] is False
    e = parse('null')
    assert e.elements[0] is None


def test_assignments():
    e = parse('a = 1')
    assert e.elements[0].subject == 'a'
    assert e.elements[0].expr.value == '1'
