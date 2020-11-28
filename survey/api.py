import sys
import types
import os
import collections

from . import io
from . import cursor
from . import bases
from . import tools
from . import helpers


__all__ = ('update', 'respond', 'edit', 'select')


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
    shows = [],
    fall = 0,
    signal = None,
    gentle = False,
)


def _finish(gentle):

    _assets.signal()

    _assets.gentle = gentle


def finish(gentle):

    """
    Stop listening for keypresses.
    """

    _finish(gentle)


def _update(value):

    _assets.machine.clear()

    _assets.caption.update(value)

    _assets.machine.draw()
    _assets.machine.focus()


def update(value):

    """
    Update hint.
    """

    with _cursor.hidden:
        _update(value)


def _respond(shows, full, color, draw, delimit):

    _assets.machine.clear()

    if shows is None:
        shows = _assets.shows.copy()

    _assets.shows.clear()

    if color:
        paint = lambda value: helpers.paint(value, color)
        shows = map(paint, shows)

    show = delimit.join(shows)

    if not full:
        show = _assets.fall * os.linesep + show

    _assets.caption.finish(show, full = full)

    if not full:
        _io.send(os.linesep)


def respond(shows = None,
            full = False,
            color = None,
            draw = True,
            delimit = ', '):

    """
    Reset state and show results.

    :param list[str] show:
        What to show instead.
    :param bool full:
        Whether to also erase prompt.
    :param str color:
        Used to paint results.
    :param bool draw:
        Whether to show results.
    :param str delimit:
        Used to join results together.
    """

    with _cursor.hidden:
        _respond(shows, full, color, draw, delimit)


def _execute(machine, check):

    _assets.machine = machine

    translator = bases.Translator(_io, callback = _assets.machine.invoke)

    source = bases.Source(_io, callback = translator.invoke)

    _assets.signal = source.done

    while True:
        source.stream()
        result = _assets.machine.get()
        if _assets.gentle and check and not check(result):
            _io.ring()
            continue
        break

    shows = machine.view(result)
    _assets.shows.extend(shows)

    return result


def _measure():

    (my, mx) = _cursor.measure()

    my -= 1
    mx -= 1

    _assets.caption.locate(mx)

    return (my, mx)


class Abort(Exception):

    __slots__ = ()


def _callback(function):

    def callback(name, *args):
        if function:
            result = _assets.machine.get()
            try:
                function(name, result, *args)
            except Abort:
                _io.ring()
                return
        if name == 'submit':
            _finish(True)

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


def _line_edit_multi(my, mx, trail, limit, funnel, callback):

    def finchk():
        init = len(editor.subs)
        subs = editor.subs[-trail:]
        result = len(subs) == trail and not any(sub.buffer for sub in subs)
        if result:
            extra = init == trail
            editor.delete(True, trail - extra)
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
         trail = 2,
         check = None,
         callback = None,
         multi = False):

    """
    Await and return input from user.

    :param str prompt:
        Persistent prompt shown before input.
    :param str hint:
        Temporary grayed-out prompt shown after prompt.
    :param int limit:
        Max allowed size of internal rune buffer.
    :param func funnel:
        Used with ``(rune)`` and must return some rune.
    :param int trail:
        Only with ``multi``. Amount of empty lines required to submit.
    :param func check:
        Used with ``(result)`` for validation and must return :class:`bool`.
    :param func callback:
        Used with ``(name, *args)`` for listening to keypress events.
    :param bool multi:
        Whether to accept line breaks.

    Event names are followed by current result, and then arguments.
    """

    (my, mx) = _measure()

    callback = _callback(callback)

    if multi:
        machine = _line_edit_multi(my, mx, trail, limit, funnel, callback)
        fall = 1
    else:
        machine = _line_edit_single(my, mx, limit, funnel, callback)
        fall = 0

    _assets.fall = fall

    _assets.caption.create(prompt or '', hint or '', fall = multi)

    value = _execute(machine, check)

    return value


def _select_single(my, mx,
                   options,
                   prefix,
                   indent,
                   funnel,
                   filter,
                   index,
                   callback):

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
        index,
        callback = callback
    )

    return select


def _select_multi(my, mx,
                  options,
                  prefix,
                  indent,
                  funnel,
                  filter,
                  index,
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
        index,
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
           index = 0,
           unpin = '[ ] ',
           pin = '[X] ',
           indexes = (),
           check = None,
           callback = None,
           multi = False):

    """
    Draw a menu of options. Traverse using **↑** and **↓** keys. Type to filter.
    Enter to submit. Return index(es) of option(s).

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
    :param int index:
        Where to place the cursor upon initial draw.
    :param str unpin:
        Indicator for un-selected items (multi only).
    :param str pin:
        Indicator for selected items (multi only).
    :param list[int] indexes:
        Indexes options to pre-select (multi only).
    :param func check:
        Used with ``(result)`` for validation and must return :class:`bool`.
    :param func callback:
        Used with ``(name, *args)`` for listening to keypress events.
    :param bool multi:
        Whether to allow multiple selections using **←** and **→** keys.

    Event names are followed by current result, and then arguments.
    """

    (my, mx) = _measure()

    if color:
        def paint(index, option):
            return helpers.paint(option, color)
        funnel = helpers.combine_functions(funnel, paint, index = 1)

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
            index,
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
            index,
            callback
        )

    _assets.fall = 0

    _assets.caption.create(prompt or '', hint or '', fall = 1)

    machine.draw()
    machine.focus()

    with _cursor.hidden:
        value = _execute(machine, check)

    return value
