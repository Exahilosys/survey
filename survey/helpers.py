import functools
import threading
import wrapio
import re
import inspect
import contextlib
import collections
import itertools


__all__ = ()


_sentinel = object()


class Atomic:

    __slots__ = ('_enter', '_leave', '_size', '_lock')

    def __init__(self, enter = None, leave = None):

        self._enter = enter
        self._leave = leave

        self._size = 0
        self._lock = threading.Lock()

    @property
    def open(self):

        return not self._size

    def _deduce(self, function, step, limit):

        with self._lock:
            size = self._size + step
            if not size > limit and function:
                function()
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


def rindex(values, sub, start = 0, stop = None):

    if stop is None:
        stop = len(values)

    pairs = tuple(enumerate(values))[start:stop]

    for (index, value) in reversed(pairs):
        if not value == sub:
            continue
        break
    else:
        raise ValueError(repr(sub) + ' not in iterable')

    return index


def split(values, sub, maxsplit = - 1):

    buffer = []
    for value in values:
        if maxsplit == 0:
            break
        if value == sub:
            yield buffer.copy()
            buffer.clear()
            maxsplit -= 1
        else:
            buffer.append(value)

    yield buffer


class seq:

    _pattern = re.compile('(\x1b[\\[0-?]*[@-~])')

    @classmethod
    def _split(cls, value):

        result = cls._pattern.split(value)

        return result

    @classmethod
    def _is_seq(cls, index):

        return index % 2

    @classmethod
    def _inspect(cls, values):

        for (index, value) in enumerate(values):
            yield (cls._is_seq(index), value)

    @classmethod
    def _clean(cls, values):

        for (is_seq, value) in cls._inspect(values):
            if is_seq:
                continue
            yield value

    @classmethod
    def clean(cls, value):

        parts = cls._split(value)
        parts = cls._clean(parts)

        result = ''.join(parts)

        return result

    @classmethod
    def trim(cls, value, size):

        parts = cls._split(value)

        pairs = enumerate(parts)
        pairs = cls._clean(parts)
        pairs = reversed(tuple(parts))

        for (index, part) in pairs:
            potential = len(part)
            limit = min(size, potential)
            cutoff = potential - limit
            parts[index] = part[:cutoff]
            size -= limit

        result = ''.join(reversed(parts))

        return result

    @classmethod
    def inject(cls, value, index, sub):

        parts = cls._split(value)

        pairs = enumerate(parts)
        pairs = cls._clean(pairs)

        limit = index
        for (index, part) in pairs:
            potential = len(part)
            if not potential < limit:
                break
            limit -= potential

        parts[index] = part[:limit] + sub + part[limit:]

        return ''.join(parts)


_make_ansi_sgr = '\x1b[{0}m'.format


_ansi_sgr_switches = tuple(
    (_make_ansi_sgr(code), set(map(_make_ansi_sgr, codes)))
    for (code, codes)
    in (
        (21, (1,)),
        (22, (1, 2,)),
        (23, (3, 20,)),
        (24, (4,)),
        (25, (5, 6)),
        (27, (6,)),
        (28, (8,)),
        (29, (9,)),
        (39, (*range(30, 39), *range(90, 98))),
        (49, (*range(40, 49), *range(100, 108))),
        (51, (54,)),
        (52, (54,)),
        (53, (55,)),
        (58, (59,))
    )
)


del _make_ansi_sgr


def paint(value, sequence, null = '\x1b[0m'):

    # replace anything that switches it off
    for (subsequence, sequences) in _ansi_sgr_switches:
        if not sequence in sequences:
            continue
        # this assumes that no sequence continues
        # after one of the same family shows up
        value = value.replace(subsequence, sequence)

    # null may be turning others off; put after
    value = value.replace(null, null + sequence)

    result = sequence + value + null

    return result


def clean(value, ignore = set()):

    exclude = set()

    for rune in value:
        if rune.isprintable():
            continue
        exclude.add(rune)

    if exclude:
        pattern = '[{0}]'.format(''.join(exclude))
        if ignore:
            pattern = '(?!{1}){0}(?<!{1})'.format(pattern, '|'.join(ignore))
        value = re.sub(pattern, '', value)

    return value


def succeed_functions(*functions):

    functions = tuple(filter(bool, functions))

    def wrapper(*args, **kwargs):
        result = None
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


def _multifilter(function, *iterables):

    (first, *rest) = map(iter, iterables)

    while True:
        try:
            value = next(first)
        except StopIteration:
            break
        values = map(next, rest)
        accept = function(value)
        values = tuple(values)
        if accept:
            yield (value, *values)


def multifilter(*args, **kwargs):

    result = _multifilter(*args, **kwargs)

    return zip(*result)


def exclude_args(kwargs, *keys, message = '{0} is overwritten'):

    for key in keys:
        if not key in kwargs:
            continue
        break
    else:
        return

    raise ValueError(message.format(key))


@functools.lru_cache(None)
def _get_signature(function):

    return inspect.signature(function)


def get_simulated_arg_index(function):

    signature = _get_signature(function)

    contribute = {
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD
    }

    index = 0
    for parameter in signature.parameters.values():
        if not parameter.kind in contribute:
            continue
        index += 1

    return index


def simulate_arg(args,
                 kwargs,
                 index = None,
                 key = None,
                 default = _sentinel,
                 name = None):

    def _fail(message):
        if name:
            message += ': ' + repr(name)
        raise TypeError(message)

    result = _sentinel

    if not index is None:
        try:
            result = args.pop(index)
        except IndexError:
            pass

    if not key is None:
        if result is _sentinel:
            try:
                result = kwargs.pop(key)
            except KeyError:
                pass
        elif key in kwargs:
            _fail('missing required argument:')

    if result is _sentinel:
        if default is _sentinel:
            _fail('missing required argument')
        result = default

    return result


def call_default(function, name, kwargs, default = inspect.Parameter.empty):

    signature = _get_signature(function)

    parameter = signature.parameters[name]

    nodefault = parameter.default is inspect.Parameter.empty

    try:
        result = kwargs[name]
    except KeyError:
        result = default if nodefault else parameter.default

    if result is inspect.Parameter.empty:
        raise TypeError('missing keyword-only argument: ' + repr(name))

    return result


@contextlib.contextmanager
def noop_contextmanager():

    yield


def compat_namedtuple(*args, defaults = (), **kwargs):

    base = collections.namedtuple(*args, **kwargs)

    stores = (base._fields, defaults)
    stores = map(reversed, stores)

    pairs = itertools.zip_longest(*stores)
    pairs = tuple(reversed(tuple(pairs)))
    pairs = pairs[- len(defaults):]

    class Nt(base):

        __slots__ = ()

        def __new__(cls, *args, **kwargs):

            read = len(args) - len(base._fields)

            if read:
                for pair in pairs[read:]:
                    kwargs.setdefault(*pair)

            return super().__new__(cls, *args, **kwargs)

    return Nt
