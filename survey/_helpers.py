import types
import functools
import operator
import re
import math
import itertools
import collections
import inspect
import copy
import contextlib
import statistics

from . import _constants


from ._core._helpers import *


class InfoErrorMixin:

    __slots__ = ()

    def __init__(self, text, **info_kwargs):

        info = types.SimpleNamespace(**info_kwargs)

        super().__init__(text, info)

    @property
    def text(self):

        return self.args[0]

    @property
    def info(self):

        return self.args[1]


def noop(*args, **kwargs):

    pass


@contextlib.contextmanager
def noop_contextmanager(*args, **kawrgs):

    yield


def text_point_to_index(lines, cy, cx):

    lines = lines[:cy]

    ci = sum(map(len, lines)) + len(lines) + cx

    return ci


def text_index_to_point(lines, ci):

    cy = 0
    cx = ci
    for sx in map(len, lines):
        sx += 1
        ci -= sx
        if ci < 0:
            break
        cy += 1
        cx = ci

    return (cy, cx)


def get_point_neighbors(origin, radius):

    steps = range(- radius, radius + 1)

    for i, j in itertools.product(steps, steps):
        if not radius in map(abs, (i, j)):
            continue
        yield (origin[0] + i, origin[1] + j)


def get_point_distance_to_point(origin, target):

    return math.sqrt(sum((px - qx) ** 2.0 for px, qx in zip(origin, target)))

def get_point_distance_to_line(slope, intercept, target):

    return abs(-slope * target[1] + target[0] - intercept) / math.hypot(slope, 1)


def get_point_direction_to_point(origin, target):

    dy = target[0] - origin[0]
    dx = target[1] - origin[1]
    
    angle = math.atan2(dy, dx)
    direction = math.degrees(angle)

    return direction


def get_point_directional(decide, origin, direction, targets, window = 90, ignore_point = False):

    angle = math.radians(direction % 180)
    slope = math.tan(angle)
    intercept = origin[0] - slope * origin[1]

    def check_direction(target):
        if target == origin:
            return False
        cur_direction = direction
        new_direction = get_point_direction_to_point(origin, target)
        return abs(new_direction - cur_direction) < window

    targets = tuple(filter(check_direction, targets))

    def get_score(target):
        distance_to_line = get_point_distance_to_line(slope, intercept, target)
        distance_to_point = get_point_distance_to_point(origin, target)
        if ignore_point:
            distance_to_line *= - 1
        return distance_to_line + distance_to_point

    target = decide(targets, key = get_score, default = origin) 

    return target
    

def get_point_directional_next(origin, direction, radius):

    points = tuple(get_point_neighbors(origin, radius))

    return get_point_directional(min, origin, direction, points)


def reverse_direction(direction):

    direction = direction % 360 - 180

    return direction if direction > - 180 else direction + 360


class SGR:

    _cre = re.compile('((?:\x1b[\\[0-?]*m)+)')

    @classmethod
    def split(cls, value):

        return cls._cre.split(value)

    @classmethod
    def yank(cls, value):

        chunks = cls.split(value)

        for index, chunk in enumerate(chunks):
            if index % 2:
                continue
            yield chunk

    @classmethod
    def clean(cls, value):

        chunks = cls.yank(value)

        return functools.reduce(operator.add, chunks)
    
    @classmethod
    def apply(cls, function, value):

        chunks = cls.split(value)

        for index, chunk in enumerate(chunks):
            if index % 2:
                continue
            chunks[index] = function(chunk)

        return ''.join(chunks)
    
    resets = {
        '\x1b[0m', 
        '\x1b[22m ','\x1b[23m', '\x1b[24m', '\x1b[25m', '\x1b[26m',' \x1b[27m','\x1b[28m',
        '\x1b[39m', '\x1b[49m', '\x1b[50m', '\x1b[54m', '\x1b[55m', '\x1b[59m', '\x1b[65m', '\x1b[75m'
    }


def chain_functions(*functions):

    functions = tuple(filter(callable, functions))

    def function(*args, **kwargs):
        for function in functions:
            function(*args, **kwargs)

    return function


def split_line(value):

    chunks = SGR.split(value)

    buffer = list(chunks.pop(0))

    for index, chunk in enumerate(chunks):
        if not index % 2:
            continue
        if chunk:
            runes = list(chunk)
            attach = chunks[index - 1]
            try:
                if attach in SGR.resets:
                    try:
                        buffer[- 1] += attach
                    except IndexError:
                        pass
                    else:
                        continue
                runes[0] = attach + runes[0]
            finally:
                buffer.extend(runes)
        else:
            # last chunk is always empty
            try:
                buffer[- 1] += chunks[index - 1]
            except IndexError:
                pass

    return buffer


def split_lines(value, *args, **kwargs):

    values = value.split(_constants.linesep)

    get = lambda value: split_line(value, *args, **kwargs)

    lines = list(map(get, values))

    return lines


def join_line(line):

    value = ''.join(line)

    return value


def join_lines(lines, *args, **kwargs):

    get = functools.partial(join_line, *args, **kwargs)

    values = map(get, lines)

    value = _constants.linesep.join(values)

    return value


class IdentifiableSGR(str):

    __slots__ = ('_names',)

    def __new__(cls, value, **names):

        self = super().__new__(cls, value)

        self._names = names

        return self
    
    def describe(self):

        parts = ((name, value) for name, value in self._names.items() if value)

        description = ' '.join(map('{0[0]}:{0[1]}'.format, parts))

        return description
    
    def __repr__(self):

        description = self.describe()

        return f'<{description}>'


def paint_rune(color, rune, reset = '\x1b[0m'):

    if color is None:
        return rune

    return color + rune + reset


class Graffity(str):

    __slots__ = ('_color', '_value')

    def __new__(cls, color, value):

        if not isinstance(color, IdentifiableSGR):
            return value

        self = super().__new__(cls, value)

        self._color = color
        self._value = value

        return self

    def __repr__(self):

        color_description = self._color.describe()
        value_description = repr(self._value)

        return f'<{color_description} {value_description}>'


def paint_text(color, value, *args, **kwargs):

    paint = functools.partial(paint_rune, color)

    value = ''.join(map(paint, value))

    return Graffity(color, value)


def paint_line(color, line, *args, **kwargs):

    for index, rune in enumerate(line):
        line[index] = paint_rune(color, rune, *args, **kwargs)


def paint_lines(color, lines, *args, **kwargs):

    for line in lines:
        paint_line(color, line, *args, **kwargs)


def merge_lines(main, *rest):

    main = copy.deepcopy(main)
    for rest in map(copy.deepcopy, rest):
        main[- 1].extend(rest.pop(0))
        main.extend(rest)

    return main


def check_lines(lines):

    return len(lines) > 1 or any(lines)


def squeeze_spots(axis, spots, dimensions = None, start = 0):

    if dimensions is None:
        dimensions = len(next(iter(spots)))

    oths = (axis - 1) % dimensions

    buckets = collections.defaultdict(list)

    for spot in spots:
        cur_a = spot[axis]
        cur_o = spot[oths]
        buckets[cur_a].append(cur_o)

    all_a = range(0, len(buckets))

    for new_a, cur_info in zip(all_a, buckets.items()):
        cur_a, all_o = cur_info
        for new_o, cur_o in enumerate(all_o, start = start):
            cur_spot = [cur_o] * 2
            cur_spot[axis] = cur_a
            new_spot = [new_o] * 2
            new_spot[axis] = new_a
            yield tuple(map(tuple, (cur_spot, new_spot)))


def decorify(function):

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return functools.partial(function, *args, **kwargs)
    
    wrapper.call = function

    wrapper.__annotations__ = function.__annotations__

    return wrapper


def get_axis_point(dimensions, axis, default, index):

    point = [default] * dimensions
    
    point[axis] = index

    return point


@functools.lru_cache()
def get_function_parameters(function):

    if isinstance(function, type):
        functions = function.__mro__
    else:
        functions = ()

    signatures = reversed(tuple(map(inspect.signature, functions)))

    ignore_kinds = {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}

    parameters = {}
    for signature in signatures:
        parameters.update(signature.parameters)

    parameters = {name: parameter for name, parameter in parameters.items() if not parameter.kind in ignore_kinds}

    return parameters


@functools.lru_cache()
def get_function_args_names(function):

    parameters = get_function_parameters(function)

    return tuple(parameters)


def get_function_args_default(function, name):

    parameters = get_function_parameters(function)

    parameter = parameters[name]

    default = parameter.default

    if default is inspect.Parameter.empty:
        raise ValueError(f'parameter "{name}" of {function} has no default')

    return default


def get_function_arg_safe(function, name, store, pop = False):

    getter = store.pop if pop else store.__getitem__

    try:
        return getter(name)
    except KeyError:
        pass

    return get_function_args_default(function, name)


def yank_dict(store, keys):

    result = {}
    for key in keys:
        try:
            value = store.pop(key)
        except KeyError:
            continue
        result[key] = value

    return result


def split_list(store, check):

    result = ([], [])

    for value in store:
        result[check(value)].append(value)

    return result


def asset_value(value):

    lines = split_lines(value)

    point_y = len(lines) - 1
    point_x = len(lines[point_y])
    point = [point_y, point_x]

    return (lines, point)


def get_or_call(value, *args, **kwargs):
    
    return value(*args, **kwargs) if callable(value) else value


auto = type('auto', (), {'__slots__': (), '__repr__': lambda self: self.__class__.__name__})()


def format_seconds(value, delimit = ':', fill = '0', depth = None):

    depth = max(0, depth - 1)

    dividers = (60, 60, 24)
    segments = []

    value = round(value)

    for divider_index, divider in enumerate(dividers):
        top, sub = divmod(value, divider)
        sub = str(sub)
        sub = fill * (len(str(divider)) - len(sub)) + sub
        segments.append(sub)
        if not top and (depth is None or not divider_index < depth):
            break
        value = top

    return delimit.join(reversed(segments))