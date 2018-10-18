from . import template
from . import utils


def test_template():
    e = template.parse('123')
    assert e.text_.text == "123"
    e = template.parse('123[]')
    assert e.text_.text == "123"


def test_calls():
    e = template.parse('123[blah]')
    assert e.elements[1].elements[0].elements[0].elements[1].text == "blah"
    e = template.parse('123[][blah]')
    assert e.elements[1].elements[1].elements[0].elements[1].text == "blah"
    e = template.parse('123[blah[a1][a2]]')
    call = e.elements[1].elements[0].elements[0].elements[1].elements[1].elements[0]
    assert call.name.text == "blah"
    assert utils.traverse(call, (1, 0, 1)).text == "a1"
    assert utils.traverse(call, (1, 1, 1)).text == "a2"
    e = template.parse('123[blah[text[Z]text]]')
    call = utils.traverse(e, (1, 0, 0, 1, 1, 0))
    innert_call = utils.traverse(call, (1, 0, 1, 1, 0, 0, 1))
    assert call.name.text == "blah"
    assert innert_call.text == "Z"
