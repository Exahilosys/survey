import functools
import threading
import wrapio
import re

from . import _colors


__all__ = ()


class Atomic:

    __slots__ = ('_enter', '_leave', '_size', '_lock')

    def __init__(self, enter, leave):

        self._enter = enter
        self._leave = leave

        self._size = 0
        self._lock = threading.Lock()

    def _deduce(self, func, step, limit):

        with self._lock:
            size = self._size + step
            if not size > limit:
                func()
            self._size = size

    def __enter__(self):

        self._deduce(self._enter, 1, 1)

    def __exit__(self, type, value, traceback):

        self._deduce(self._leave, - 1, 0)


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


def _color_split(value):

    parts = seq.split(value)

    buffer = []
    for (index, part) in enumerate(parts):
        if index % 2 and part.endswith('m'):
            yield ''.join(buffer)
            yield part
            buffer.clear()
            continue
        buffer.append(part)

    yield ''.join(buffer)


_null_color = _colors.null


def _color_smear(value, color):

    parts = _color_split(value)

    depth = 0
    for (index, part) in enumerate(parts):
        if not index % 2:
            yield part
            continue
        if part == _null_color:
            depth -= 1
            if not depth:
                part = color
        else:
            depth += 1
        yield part


def paint(value, color):

    if not color:
        return value

    parts = _color_smear(value, color)
    parts = tuple(parts)

    return color + ''.join(parts) + _null_color


def clean(value, keep = set()):

    for rune in value:
        if not rune.isprintable() and not rune in keep:
            continue
        yield rune


def succeed_functions(*functions):

    functions = tuple(filter(bool, functions))

    def wrapper(*args, **kwargs):
        for function in functions:
            result = function(*args, **kwargs)
        return result

    return wrapper


def combine_functions(*functions, index = 0):

    functions = tuple(filter(bool, functions))

    def wrapper(*args, **kwargs):
        args = list(args)
        for function in functions:
            args[index] = function(*args, **kwargs)
        return args[index]

    return wrapper


def _multifilter(func, *iterables):

    (first, *rest) = map(iter, iterables)

    while True:
        try:
            value = next(first)
        except StopIteration:
            break
        values = map(next, rest)
        accept = func(value)
        values = tuple(values)
        if accept:
            yield (value, *values)


def multifilter(*args, **kwargs):

    result = _multifilter(*args, **kwargs)

    return zip(*result)


def exclude_arg(kwargs, key, message = '{0} is overwritten'):
    if not key in kwargs:
        return
    raise ValueError(message.format(key))
