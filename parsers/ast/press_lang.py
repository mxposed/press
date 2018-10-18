

class String:
    def __init__(self, value):
        self.value = value


class Number:
    def __init__(self, value):
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
