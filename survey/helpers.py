import wrapio
import re


__all__ = ()


class Handle(wrapio.Handle):

    __slots__ = ()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs, sync = True)

    def invoke(self, *args, **kwargs):

        try:
            super().invoke(*args, **kwargs)
        except KeyError:
            fail = True
        else:
            fail = False

        return fail


def paint(value, color, null = '\x1b[0m'):

    return color + value + null


class seq:

    _pattern = re.compile('(\x1b[\\[0-?]*[@-~])')

    @classmethod
    def split(cls, value):

        return cls._pattern.split(value)

    @classmethod
    def clean(cls, value):

        parts = cls.split(value)

        store = []
        for (index, part) in enumerate(parts):
            if index % 2:
                continue
            store.append(part)

        return ''.join(store)

    @classmethod
    def trim(cls, value, size):

        parts = cls.split(value)

        parts = list(reversed(parts))

        for (index, part) in enumerate(parts):
            if index % 2:
                continue
            potential = len(part)
            limit = min(size, potential)
            cutoff = potential - limit
            parts[index] = part[:cutoff]
            size -= limit

        return ''.join(reversed(parts))

    @classmethod
    def inject(cls, value, index, sub):

        parts = cls.split(value)

        state = index
        for (index, part) in enumerate(parts):
            if index % 2:
                continue
            potential = len(part)
            if not potential < state:
                break
            state -= potential

        parts[index] = part[:state] + sub + part[state:]

        return ''.join(parts)


def clean(value, keep = set()):

    for rune in value:
        if not rune.isprintable() and not rune in keep:
            continue
        yield rune


def combine_functions(*functions, index = 0):

    check = lambda function: not function is None

    functions = tuple(filter(check, functions))

    def wrapper(*args, **kwargs):
        args = list(args)
        for function in functions:
            args[index] = function(*args, **kwargs)
        return args[index]

    return wrapper
