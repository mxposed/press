from runtime import Runtime, NameResolutionError, PressError


def prepare_arg(caller, runtime, arg):
    if isinstance(arg, Number):
        if '.' in arg.value:
            return float(arg.value)
        else:
            return int(arg.value)
    elif isinstance(arg, String):
        return eval(arg.value)
    elif isinstance(arg, List):
        return list(map(lambda el: prepare_arg(caller, runtime, el), arg.elements))
    elif isinstance(arg, Object):
        pairs = []
        for pair in arg.elements:
            pairs.append((prepare_arg(caller, runtime, pair.key),
                          prepare_arg(caller, runtime, pair.value)))
        return dict(pairs)
    elif hasattr(arg, 'execute'):
        if hasattr(arg, 'lazy'):
            if arg.lazy:
                arg.lazy = False
                return arg
            else:
                return arg.execute(runtime, caller=caller)
        else:
            return arg.execute(runtime, caller=caller)
    else:
        return arg


class Node:
    child_attr = 'elements'

    def __init__(self, *args, start=None, end=None) -> None:
        super().__init__()
        self.start = start
        self.end = end
        self.caller = None
        self.parent = None
        self.root = None
        self.prefix = None

    def set_parent(self, parent):
        if parent is not None:
            root = parent.root
        else:
            root = self
        if self.parent is None:
            self.parent = parent
            self.root = root

        if self.has_children():
            for child in self.children():
                if isinstance(child, Node):
                    child.set_parent(self)

    def has_children(self):
        return hasattr(self, self.__class__.child_attr)

    def children(self):
        return getattr(self, self.__class__.child_attr)

    @property
    def prefix_lines(self):
        if self.prefix is None:
            return 0
        return self.prefix.count('\n')


class String(Node):
    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value


class Number(Node):
    def __init__(self, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return '<Number: {}>'.format(self.value)


class Call(Node):
    def __init__(self, subject, args, *pargs, **kwargs):
        super().__init__(*pargs, **kwargs)
        self.subject = subject
        self.args = args

    def execute(self, runtime: Runtime, caller: Node = None):
        self.caller = caller

        if runtime.has(self.subject):
            subject = runtime.get(self.subject)
            args = self.prepare_args(runtime)
            if callable(subject):
                try:
                    return subject(runtime, *args, caller=self)
                except Exception as e:
                    raise PressError(e, node=self)
            elif hasattr(subject, 'execute'):
                return subject.execute(runtime, *args, caller=self)
            else:
                return subject
        else:
            raise NameResolutionError(self.subject, node=self)

    def prepare_args(self, runtime):
        result = []
        for arg in self.args:
            result.append(prepare_arg(self, runtime, arg))
        return result

    def has_children(self):
        return True

    def children(self):
        return self.args + [self.subject]


class Assignment(Node):
    def __init__(self, subject, expr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subject = subject
        self.expr = expr

    def execute(self, runtime, caller: Node = None):
        self.caller = caller

        expr = self.expr
        if hasattr(expr, 'execute') and not isinstance(self.expr, Function):
            expr = expr.execute(runtime, caller=self)
        runtime.set(self.subject, expr)

    def has_children(self):
        return True

    def children(self):
        return [self.subject, self.expr]


class Function(Node):
    def __init__(self, args, code, *pargs, **kwargs):
        super().__init__(*pargs, **kwargs)
        self.args = args
        self.code = code

    def execute(self, runtime, *args, caller: Node = None):
        self.caller = caller

        runtime.push()
        for i, arg in enumerate(args):
            runtime.set(self.args[i], arg)
        self.code.execute(runtime, caller=self)
        runtime.pop()

    def has_children(self):
        return True

    def children(self):
        return self.args + [self.code]


class Statements(Node):
    def __init__(self, exprs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elements = exprs

    def execute(self, runtime, caller: Node = None):
        self.caller = caller

        for expr in self.elements:
            if hasattr(expr, 'execute'):
                expr.execute(runtime, caller=self)


class List(Node):
    def __init__(self, elements, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elements = elements


class Object(Node):
    def __init__(self, elements, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elements = elements


class Pair(Node):
    def __init__(self, key, value, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.key = key
        self.value = value

    def has_children(self):
        return True

    def children(self):
        return [self.key, self.value]


class Actions:
    @staticmethod
    def make_name(input, start, end, elements):
        return input[start:end]

    @staticmethod
    def make_none(input, start, end):
        return None

    @staticmethod
    def make_number(input, start, end, elements):
        return Number(input[start:end], start=start, end=end)

    @staticmethod
    def make_string(input, start, end, elements):
        return String(input[start:end], start=start, end=end)

    @staticmethod
    def make_boolean(input, start, end):
        if input[start:end] == "true":
            return True
        return False

    @staticmethod
    def make_statements(input, start, end, elements):
        exprs = []
        if hasattr(elements[1], 'expr'):
            exprs.append(elements[1].expr)
        if hasattr(elements[1], 'exprs'):
            for el in elements[1].exprs:
                exprs.append(el.expr)
        return Statements(exprs, start=start, end=end)

    @staticmethod
    def make_call(input, start, end, elements):
        args = []
        if hasattr(elements[1], 'args'):
            call_args = elements[1].args
            if hasattr(call_args, 'basic_expr'):
                args.append(elements[1].args.basic_expr)
            if hasattr(call_args, 'exprs') and call_args.exprs.elements:
                for arg in call_args.exprs.elements:
                    args.append(arg.basic_expr)
        elif hasattr(elements[1], 'basic_expr'):
            args.append(elements[1].basic_expr)
        elif elements[1].elements and hasattr(elements[1].elements[0],
                                              'inner_template'):
            for template in elements[1].elements:
                args.append(template.inner_template)
        return Call(elements[0], args, start=start, end=end)

    @staticmethod
    def make_assignment(input, start, end, elements):
        return Assignment(elements[0], elements[4], start=start, end=end)

    @staticmethod
    def make_function(input, start, end, elements):
        args = []
        code = elements[7]
        if elements[3].elements:
            args.append(elements[3].elements[1])
            if len(elements[3].elements) > 3:
                for el in elements[3].elements[3]:
                    args.append(el.elements[2])
        return Function(args, code, start=start, end=end)

    @staticmethod
    def make_list(input, start, end, elements):
        els = [elements[2]]
        if elements[4].elements:
            for el in elements[4].elements:
                els.append(el.elements[2])
        return List(els, start=start, end=end)

    @staticmethod
    def make_object(input, start, end, elements):
        if len(elements) < 4:
            return Object([])
        pairs = [elements[2]]
        if elements[4].elements:
            for el in elements[4].elements:
                pairs.append(el.elements[2])
        return Object(pairs, start=start, end=end)

    @staticmethod
    def make_pair(input, start, end, elements):
        return Pair(elements[0], elements[4], start=start, end=end)
