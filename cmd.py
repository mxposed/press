import re


class Command:
    def __init__(self, command):
        self.command = command

    def apply(self, doc, text):
        m = re.match(r'size (\d+)', self.command)
        if m:
            size = int(m.group(1))
            text.setFont(text._fontname, size)

    def __str__(self):
        return 'Command: <{}>'.format(repr(self.command))

    def __repr__(self):
        return str(self)
