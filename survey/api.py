import sys
import types
import os
import collections

from . import io
from . import cursor
from . import bases
from . import tools
from . import helpers


__all__ = ('edit', 'select')


_io = io.IO(sys.stdin, sys.stdout)


_cursor = cursor.Cursor(_io)


_assets = types.SimpleNamespace(
    caption = tools.Caption(
        tools.Display(
            _io,
            _cursor
        )
    ),
    machine = None,
    results = [],
    bellow = 0,
    signal = None,
)


def _update(value):

    _assets.machine.clear()

    _assets.caption.update(value)

    _assets.machine.draw()
    _assets.machine.focus()


def update(value):

    with _cursor.hidden:
        _update(value)


def _respond(color, draw, delimit):

    _assets.machine.clear()

    results = []
    while True:
        try:
            result = _assets.results.pop(0)
        except IndexError:
            break
        if not draw:
            continue
        results.append(result)

    if color:
        paint = lambda value: helpers.paint(value, color)
        results = map(paint, results)

    result = delimit.join(results)

    _assets.caption.finish(result, fall = _assets.bellow)

    _io.send(os.linesep)


def respond(color = None, draw = True, delimit = ', '):

    with _cursor.hidden:
        _respond(color, draw, delimit)


def _execute(machine, check, view):

    _assets.machine = machine

    translator = bases.Translator(_io, callback = machine.invoke)

    source = bases.Source(_io, callback = translator.invoke)

    _assets.signal = source.done

    while True:
        source.stream()
        value = machine.get()
        if check and not check(value):
            _io.ring()
            continue
        break

    results = (view if view else machine.view)(value)

    _assets.results.extend(results)

    return value


def _measure():

    (my, mx) = _cursor.measure()

    my -= 1
    mx -= 1

    _assets.caption.locate(mx)

    return (my, mx)


def _callback(function):

    def callback(name, *args):
        if function:
            result = _assets.machine.get()
            function(name, result, *args)
        if name == 'submit':
            _assets.signal()

    return callback


def _line_edit_single(my, mx, limit, funnel, callback):

    editor = tools.LineEditor(
        _io,
        _cursor,
        mx,
        limit,
        funnel,
        callback = callback
    )

    return editor


def _line_edit_multi(my, mx, finish, limit, funnel, callback):

    def finchk():
        subs = editor.subs[-finish:]
        result = len(subs) == finish and not any(sub.buffer for sub in subs)
        if result:
            editor.delete(True, finish)
        return result

    editor = tools.MultiLineEditor(
        _io,
        _cursor,
        finchk,
        my,
        mx,
        limit,
        funnel,
        callback = callback
    )

    return editor


def edit(prompt = None,
         *,
         hint = None,
         limit = None,
         funnel = None,
         check = None,
         finish = 2,
         callback = None,
         view = None,
         multi = False):

    """
    Await and return ``(input, display)`` from user.

    This should not be used directly for most purposes.

    :param str prompt:
        Persistent prompt shown before input.
    :param str hint:
        Temporary grayed-out prompt shown after prompt.
    :param int limit:
        Max allowed size of internal rune buffer.
    :param func funnel:
        Used with ``(rune)`` and must return some rune.
    :param func check:
        Used with ``(answer)`` for validation and must return :class:`bool`.
    :param int finish:
        Only with ``multi``. Amount of empty lines required to submit.
    :param func callback:
        Used with ``(name, *args)`` for listening to keypress events.
    :param bool multi:
        Whether to accept line breaks.
    """

    (my, mx) = _measure()

    callback = _callback(callback)

    if multi:
        machine = _line_edit_multi(my, mx, finish, limit, funnel, callback)
        bellow = 1
    else:
        machine = _line_edit_single(my, mx, limit, funnel, callback)
        bellow = 0

    _assets.bellow = bellow

    _assets.caption.create(prompt or '', hint or '', fall = multi)

    value = _execute(machine, check, view)

    return value


def _select_single(my, mx, options, prefix, indent, funnel, filter, callback):

    select = tools.Select(
        _io,
        _cursor,
        my,
        mx,
        options,
        prefix,
        indent,
        funnel,
        filter,
        callback = callback
    )

    return select


def _select_multi(my, mx,
                  options,
                  prefix,
                  indent,
                  funnel,
                  filter,
                  unpin,
                  pin,
                  indexes,
                  callback):

    select = tools.MultiSelect(
        unpin,
        pin,
        indexes,
        _io,
        _cursor,
        my,
        mx,
        options,
        prefix,
        indent,
        funnel,
        filter,
        callback = callback
    )

    return select


def _select_filter(pairs, argument):

    argument = argument.lower()

    counter = collections.Counter(argument)

    for (index, option) in pairs:
        option = option.lower()
        for (rune, rcount) in counter.items():
            ccount = option.count(rune)
            if 0 < ccount >= rcount:
                continue
            break
        else:
            yield (index, option)


def select(options,
           prompt = None,
           *,
           hint = None,
           prefix = '> ',
           color = None,
           indent = None,
           funnel = None,
           filter = None,
           limit = 6,
           unpin = '[ ] ',
           pin = '[X] ',
           indexes = (),
           callback = None,
           view = None,
           multi = False):

    """
    Draw a menu of options. Traverse using **↑** and **↓** keys. Type to filter.
    Enter to submit.

    This should not be used directly for most purposes.

    :param str prompt:
        Persistent prompt shown before input.
    :param str hint:
        Temporary grayed-out prompt shown after prompt.
    :param str prefix:
        Indicator for unpinned item.
    :param str color:
        ANSI color sequence to paint unpinned item.
    :param func funnel:
        Used with current ``(option)`` and must return some :class:`str`.
    :param int limit:
        Max amount of options displayed at any point.
    :param str unpin:
        Indicator for un-selected items (multi only).
    :param str pin:
        Indicator for selected items (multi only).
    :param list[int] indexes:
        Indexes options to pre-select (multi only).
    :param func callback:
        Used with ``(name, *args)`` for listening to keypress events.
    :param bool multi:
        Whether to allow multiple selections using **←** and **→** keys.
    """

    (my, mx) = _measure()

    if color:
        def paint(option):
            return helpers.paint(option, color)
        funnel = helpers.combine_functions(funnel, paint)

    if not limit:
        limit = len(options)
    my = min(my, limit)

    pushers = [len(prefix)]
    if indent:
        pushers.append(indent)
    cover = max(pushers)
    if multi:
        cover += max(map(len, (unpin, pin)))

    mx -= cover

    callback = _callback(callback)

    if not filter:
        filter = _select_filter

    if multi:
        machine = _select_multi(
            my, mx,
            options,
            prefix,
            indent,
            funnel,
            filter,
            unpin,
            pin,
            indexes,
            callback
        )
    else:
        machine = _select_single(
            my, mx,
            options,
            prefix,
            indent,
            funnel,
            filter,
            callback
        )

    _assets.bellow = 0

    _assets.caption.create(prompt or '', hint or '', fall = 1)

    machine.draw()
    machine.focus()

    with _cursor.hidden:
        value = _execute(machine, None, view)

    return value
