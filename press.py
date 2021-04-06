import re
import sys

from doc import Document
from runtime import PressError


def main(file):
    doc = Document(file)
    input = open(file).read()
    border = re.compile('^-{20,}$', re.MULTILINE)
    if re.search(border, input):
        intro, text = re.split(border, input, 1)
    else:
        intro, text = "", input
    doc.init(intro)
    try:
        doc.render(text)
    except PressError as e:
        e.report()
    doc.save()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: {} <file>'.format(sys.argv[0]), file=sys.stderr)
        print('  Missing required argument <file>', file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
