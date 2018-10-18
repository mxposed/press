import re
import os
import sys

from doc import Document


def main(file):
    fname = os.path.splitext(file)[0]
    doc = Document(fname)
    input = open(file).read()
    border = re.compile('^-{20,}$', re.MULTILINE)
    intro, text = re.split(border, input, 1)
    doc.init(intro)
    doc.render(text)
    doc.save()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: {} <file>'.format(sys.argv[0]), file=sys.stderr)
        print('  Missing required argument <file>', file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
