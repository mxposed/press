from runtime import Runtime


class String:
    def __init__(self, value):
        self.value = value


class Number:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return '<Number: {}>'.format(self.value)


class Call:
    def __init__(self, subject, args):
        self.subject = subject
        self.args = args

    def execute(self, runtime: Runtime):
        if runtime.has(self.subject):
            subject = runtime.get(self.subject)
            args = self.prepare_args(runtime)
            if callable(subject):
                return subject(runtime, *args)
            elif hasattr(subject, 'execute'):
                return subject.execute(runtime, *args)
            else:
                return subject
        else:
            raise ValueError('Function {} not found'.format(self.subject))

    def prepare_arg(self, runtime, arg):
        if isinstance(arg, Number):
            if '.' in arg.value:
                return float(arg.value)
            else:
                return int(arg.value)
        elif isinstance(arg, String):
            return eval(arg.value)
        elif isinstance(arg, List):
            return list(map(lambda el: self.prepare_arg(runtime, el), arg.elements))
        elif isinstance(arg, Object):
            pairs = []
            for pair in arg.elements:
                pairs.append((self.prepare_arg(runtime, pair.key),
                              self.prepare_arg(runtime, pair.value)))
            return dict(pairs)
        elif hasattr(arg, 'execute'):
            if hasattr(arg, 'lazy'):
                if arg.lazy:
                    arg.lazy = False
                    return arg
                else:
                    return arg.execute(runtime)
            else:
                return arg.execute(runtime)
        else:
            return arg

    def prepare_args(self, runtime):
        result = []
        for arg in self.args:
            result.append(self.prepare_arg(runtime, arg))
        return result


class Assignment:
    def __init__(self, subject, expr):
        self.subject = subject
        self.expr = expr

    def execute(self, runtime):
        expr = self.expr
        if hasattr(expr, 'execute') and not isinstance(self.expr, Function):
            expr = expr.execute(runtime)
        runtime.set(self.subject, expr)


class Function:
    def __init__(self, args, code):
        self.args = args
        self.code = code

    def execute(self, runtime, *args):
        runtime.push()
        for i, arg in enumerate(args):
            runtime.set(self.args[i], arg)
        self.code.execute(runtime)
        runtime.pop()


class Statements:
    def __init__(self, exprs):
        self.elements = exprs

    def execute(self, runtime):
        for expr in self.elements:
            if hasattr(expr, 'execute'):
                expr.execute(runtime)


class List:
    def __init__(self, elements):
        self.elements = elements


class Object:
    def __init__(self, elements=None):
        if elements is None:
            elements = []
        self.elements = elements


class Pair:
    def __init__(self, key, value) -> None:
        self.key = key
        self.value = value


class Actions:
    @staticmethod
    def make_name(input, start, end, elements):
        return input[start:end]

    @staticmethod
    def make_none(input, start, end):
        return None

    @staticmethod
    def make_number(input, start, end, elements):
        return Number(input[start:end])

    @staticmethod
    def make_string(input, start, end, elements):
        return String(input[start:end])

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
        return Statements(exprs)

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
        return Call(elements[0], args)

    @staticmethod
    def make_assignment(input, start, end, elements):
        return Assignment(elements[0], elements[4])

    @staticmethod
    def make_function(input, start, end, elements):
        args = []
        code = elements[7]
        if elements[3].elements:
            args.append(elements[3].elements[1])
            if len(elements[3].elements) > 3:
                for el in elements[3].elements[3]:
                    args.append(el.elements[2])
        return Function(args, code)

    @staticmethod
    def make_list(input, start, end, elements):
        els = [elements[2]]
        if elements[4].elements:
            for el in elements[4].elements:
                els.append(el.elements[2])
        return List(els)

    @staticmethod
    def make_object(input, start, end, elements):
        if len(elements) < 4:
            return Object()
        pairs = [elements[2]]
        if elements[4].elements:
            for el in elements[4].elements:
                pairs.append(el.elements[2])
        return Object(pairs)

    @staticmethod
    def make_pair(input, start, end, elements):
        return Pair(elements[0], elements[4])
