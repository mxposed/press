import inspect
import sys
from collections import defaultdict
from copy import copy
from functools import wraps
from typing import Callable

from text_fragment import State, TextFragment, TextLine


def register(func: Callable[..., None]) -> Callable[..., None]:
    Runtime.registry[func.__name__] = func
    return func


class PressError(Exception):

    def __init__(self, *args: object, **kwargs: object) -> None:
        node = kwargs['node']
        del kwargs['node']
        super().__init__(*args, **kwargs)
        self.node = node

    def report(self):
        print('Traceback:', file=sys.stderr)
        stacktrace = self.stacktrace()
        for item in stacktrace[:-1]:
            print('  {}, line {}'.format(item['file'], item['line_no']), file=sys.stderr)
            print('    {}'.format(item['line']), file=sys.stderr)
        print('{}: {}'.format(self.__class__.__name__, self.args[0]), file=sys.stderr)

        prog = self.node.root.text[:self.node.end] # type: str
        prev = prog[:self.node.start].rfind('\n')
        print('  {}'.format(stacktrace[-1]['line']), file=sys.stderr)
        print('  {}^'.format('-' * (self.node.start - prev - 1)), file=sys.stderr)
        print('  {}, line {}'.format(stacktrace[-1]['file'], stacktrace[-1]['line_no']), file=sys.stderr)

    def stacktrace(self):
        from parsers.ast.press_lang import Call

        prog = self.node.root.text[:self.node.end + 1] # type: str
        prev = prog[:self.node.start].rfind('\n')
        next = prog.find('\n', self.node.start)
        result = [{
            'file': self.node.root.file,
            'line_no': 1 + self.node.root.text[:self.node.start].count('\n') + self.node.root.prefix_lines,
            'line': prog[prev + 1:next]
        }]
        caller = self.node.caller
        while caller is not None:
            if isinstance(caller, Call):
                prog = caller.root.text[:caller.end + 1] # type: str
                prev = prog[:caller.start].rfind('\n')
                next = prog.find('\n', caller.start)
                result.append({
                    'file': caller.root.file,
                    'line_no': 1 + caller.root.text[:caller.start].count('\n') + caller.root.prefix_lines,
                    'line': prog[prev + 1:next]
                })
            elif isinstance(caller, PythonCall):
                result.append({
                    'file': caller.file,
                    'line_no': caller.line_no,
                    'line': caller.line
                })

            caller = caller.caller
        result.reverse()
        return result


class NameResolutionError(PressError):

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)


class Runtime:
    registry = {}

    def __init__(self):
        # noinspection PyUnresolvedReferences
        import runtime_funcs
        self.stack = [{}]
        self.load_registry()
        self.state = State()
        self.items = []
        self.newlines_active = True
        self.column_state = None

    def load_registry(self):
        for name, func in self.registry.items():
            self.set(name, self.decorate(func))

    def add_text(self, text):
        if self.newlines_active:
            self.items[-1].append(TextFragment(text, copy(self.state)))
            self.state.reset()

    def add_line(self, text):
        self.items[-1].append(TextLine(text, copy(self.state)))
        self.state.reset()

    def push_buffer(self):
        self.items.append([])

    def pop_buffer(self):
        return self.items.pop()

    def get(self, key):
        for d in reversed(self.stack):
            if key in d:
                return d[key]
        raise KeyError(key)

    def set(self, key, value):
        self.stack[-1][key] = value

    def push(self):
        self.stack.append({})

    def pop(self):
        self.stack.pop()

    def has(self, key):
        for d in self.stack:
            if key in d:
                return True
        return False

    def _reset_columns(self):
        self.column_state = defaultdict(int)
        self.column_state['previous'] = None

    def decorate(self, func):
        if 'caller' in inspect.signature(func).parameters:
            return func
        else:
            @wraps(func)
            def no_caller(*args, **kwargs):
                del kwargs['caller']
                return func(*args, **kwargs)
            return no_caller


class PythonCall:
    def __init__(self, caller):
        self.caller = caller
        frame = inspect.stack()[1]
        self.file = frame.filename
        self.line_no = frame.lineno
        self.line = frame.code_context[frame.index]
