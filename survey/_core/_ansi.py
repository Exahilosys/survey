import typing
import collections


__all__ = ('Text', 'Control', 'Escape', 'Sequence', 'parse', 'parse_iterable', 'get_escape', 'get_control')


Text = collections.namedtuple('Text', 'rune')
"""
Non-ANSI text.
"""

Control = collections.namedtuple('Control', 'rune')
"""
ANSI control code (`wiki <https://en.wikipedia.org/wiki/ANSI_escape_code#C0_control_codes>`__).
"""

Escape = collections.namedtuple('Escape', 'rune')
"""
ANSI escape sequence (`wiki <https://en.wikipedia.org/wiki/ANSI_escape_code#Fe_Escape_sequences>`__).
"""

Sequence = collections.namedtuple('Sequence', 'rune args trail')
"""
ANSI control sequence (`wiki <https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_(Control_Sequence_Introducer)_sequences>`__).
"""


_BITS_CODE_C0_RANGE = {*range(0,  32), 127}

_BITS_ESCAPE = 27

_BITS_CODE_C1_RANGE = {*range(64, 96)}

_BITS_SEQUENCE_INTRODUCER = 91

_BITS_SEQUENCE_PARAM_ENTER_RANGE = {*range(48, 64)}

_BITS_SEQUENCE_PARAM_SEPARATOR = 59

_BITS_SEQUENCE_PARAM_LEAVE_RANGE = {*range(32, 48)}

_BITS_SEQUENCE_FINAL_RANGE = {*range(64, 127)}


def _parse_sequence(get):

    def join(store):
        return ''.join(store)

    def update(buffer, store):
        store.append(join(buffer))
        buffer.clear()

    buffer = []
    params = []
    while True:
        rune = get()
        bits = ord(rune)
        if bits == _BITS_SEQUENCE_PARAM_SEPARATOR:
            if not buffer:
                buffer.append('0')
            update(buffer, params)
        elif bits in _BITS_SEQUENCE_PARAM_ENTER_RANGE:
            buffer.append(rune)
        else:
            break

    if buffer:
        update(buffer, params)

    trail = []
    while True:
        if bits in _BITS_SEQUENCE_PARAM_LEAVE_RANGE:
            buffer.append(rune)
        else:
            break
        rune = get()
        bits = ord(rune)

    trail = join(trail)

    # if not bits in _BITS_SEQUENCE_FINAL_RANGE:
    #     raise RuntimeError(
    #         'unexpected sequence rune: {0}'.format(rune)
    #     )

    params = tuple(params)

    return Sequence(rune, params, trail)


def _parse_escape(get):

    rune = get()
    bits = ord(rune)

    if bits == _BITS_SEQUENCE_INTRODUCER:
        return _parse_sequence(get)

    # if len(rune) and not bits in _BITS_CODE_C1_RANGE:
    #     raise RuntimeError(
    #         'unexpected escape rune: {0}'.format(rune)
    #     )

    return Escape(rune)


def _parse_stream(get):

    memo = []

    def function():
        for _ in range(2):
            try:
                rune = memo.pop(0)
            except IndexError:
                text = get()
                memo.extend(text)
            else:
                break
        try:
            rune
        except NameError:
            rune = ''
        return rune

    return function


def _parse(get):

    get = _parse_stream(get)

    rune = get()
    bits = ord(rune)

    if bits in _BITS_CODE_C0_RANGE:
        if bits == _BITS_ESCAPE:
            return _parse_escape(get)
        return Control(rune)

    return Text(rune)


_type_parse_return: typing.TypeAlias = Text | Escape | Control | Sequence


def parse(get: typing.Callable[[], str]) -> _type_parse_return:

    """
    Parse an incoming series of characters into their ANSI representation.
     
    :param get:
        Used whenever an additional character is needed, may return an empty string.

    :return:
        Encapsulates resulting ANSI information.
    """

    return _parse(get)


def _parse_iterable(iterable):

    iterator = iter(iterable)

    return _parse(iterator.__next__)


def parse_iterable(iterable: typing.Iterable) -> _type_parse_return:

    """
    Same as :func:`.parse`, except accepts an iterable.

    :param iterable:
        Its :code:`iter(...).__next__` method is used as :paramref:`.parse.get`.

    :return:
        Same as in :func:`.parse`.
    """

    return _parse_iterable(iterable)


_TEXT_ESCAPE = chr(_BITS_ESCAPE)

_TEXT_SEQUENCE_INTRODUCER = chr(_BITS_SEQUENCE_INTRODUCER)

_TEXT_SEQUENCE_INTRODUCER_CONTROL = _TEXT_ESCAPE + _TEXT_SEQUENCE_INTRODUCER

_TEXT_SEQUENCE_PARAM_SEPARATOR = chr(_BITS_SEQUENCE_PARAM_SEPARATOR)

_TEXT_SEQUENCE_PRIVATE_FLAG = '?'


def _get(prefix, code, *args):

    args = ('' if arg is None else str(arg) for arg in args)

    body = _TEXT_SEQUENCE_PARAM_SEPARATOR.join(args)

    return prefix + body + code


def _get_escape(*args):

    code = _TEXT_ESCAPE

    return _get(code, *args)


def get_escape(code: str, *args) -> str:

    """
    Get the escape sequence of ``code`` with ``args``.
    """

    return _get_escape(code, *args)


def _get_control(private, *args):

    flag = _TEXT_SEQUENCE_PRIVATE_FLAG if private else ''

    code = _TEXT_SEQUENCE_INTRODUCER_CONTROL + flag

    return _get(code, *args)


def get_control(code: str, *args, private = False) -> str:

    """
    Get the control sequence of ``code`` with ``args``.
    """

    return _get_control(private, code, *args)
