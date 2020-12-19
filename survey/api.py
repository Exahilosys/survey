import sys
import types
import wrapio
import functools
import os
import collections

from . import io
from . import cursor
from . import tools
from . import machines
from . import display
from . import helpers


__all__ = ()


# [measure] > (visualize) > [edit / select] > (update) > (finish) > [respond]


_io = io.IO(sys.stdin, sys.stdout)


setup = _io.setup


reset = _io.reset


_cursor = cursor.Cursor(_io)


_display = display.Display(_io, _cursor)


_context = types.SimpleNamespace(
    size = None,
    machine = None,
    finish = None,
    gentle = None,
    shows = [],
    fall = None
)


def view(*shows):

    _context.shows.clear()

    _context.shows.extend(shows)


def _respond(format, full, delimit):

    _context.machine.clear()

    shows = _context.shows

    if not format is None:
        shows = format(shows)

    show = delimit.join(shows)

    if not full:
        show = _context.fall * os.linesep + show

    _display.finish(show, full = full)

    if not full:
        _io.send(os.linesep)

    _context.shows.clear()


def respond(format, full, delimit):

    with _cursor.hidden:
        _respond(format, full, delimit)


def _finish(gentle):

    _context.finish()

    _context.gentle = gentle


def finish(gentle):

    with _cursor.hidden:
        _finish(gentle)


def _update(*values):

    _context.machine.clear()

    _display.update(*values)

    _context.machine.draw()
    _context.machine.focus()


def update(*values):

    with _cursor.hidden:
        _update(*values)


def _measure():

    (my, mx) = _cursor.measure()

    my -= 1
    mx -= 1

    _display.locate(mx)

    _context.size = (my, mx)


class Abort(Exception):

    __slots__ = ()


def _execute(machine, prepare, check):

    _context.machine = machine

    translator = tools.Translator(_io, callback = machine.invoke)

    source = tools.Source(_io, callback = translator.invoke)

    _context.finish = source.done

    prepare()

    while True:
        source.stream()
        result = machine.get()
        if check and _context.gentle and not check(result):
            _io.ring()
            continue
        break

    shows = machine.view(result)

    _context.shows.extend(shows)

    return result


def _automatic_wrap(faller,
                    context,
                    creator,
                    *args,
                    check = None,
                    visuals = (),
                    **kwargs):

    _measure()

    is_null = lambda visual: visual is None

    fall = faller(args, kwargs)

    if all(map(is_null, visuals)):
        visuals = (None,) # need
        fall = _context.fall = 0

    _display.create(*visuals, fall = fall)

    (machine, prepare) = creator(*args, **kwargs)

    with _cursor.hidden:
        machine.draw()
        machine.focus()

    with context:
        result = _execute(machine, prepare, check)

    return result


def _automatic(faller, hide):

    def decorator(creator):
        @functools.wraps(creator)
        def wrapper(*args, **kwargs):
            context = _cursor.hidden if hide else helpers.noop_contextmanager()
            return _automatic_wrap(faller, context, creator, *args, **kwargs)
        return wrapper

    return decorator


def _callback(function):

    track = wrapio.Track()

    @track.call
    def submit():
        _finish(True)

    callbacks = [track.invoke]

    if function:
        def callback(name, *values):
            result = _context.machine.get()
            try:
                function(name, result, *values)
            except Abort:
                _io.ring()
        callbacks.append(callback)

    callback = helpers.succeed_functions(*callbacks)

    return callback


def _edit_size():

    (my, mx) = _context.size

    return (my, mx)


def _edit_size_single():

    (my, mx) = _edit_size()

    return (my, mx)


def _edit_machine_single(limit, funnel, callback):

    (my, mx) = _edit_size_single()

    editor = machines.LineEditor(
        _io,
        _cursor,
        mx,
        limit,
        funnel,
        callback = callback
    )

    return editor


def _edit_machine_multi_finchk(editor, limit):

    size = len(editor.subs)

    subs = editor.subs[-limit:]

    result = len(subs) == limit and not any(sub.buffer for sub in subs)

    if result:
        extra = size == limit
        editor.delete(True, limit - extra)

    return result


def _edit_size_multi():

    (my, mx) = _edit_size()

    return (my, mx)


def _edit_machine_multi(trail, limit, funnel, indent, callback):

    finchk = lambda: _edit_machine_multi_finchk(editor, trail)

    (my, mx) = _edit_size_multi()

    editor = machines.MultiLineEditor(
        _io,
        _cursor,
        finchk,
        my,
        mx,
        limit,
        funnel,
        indent,
        callback = callback
    )

    return editor


def _edit_faller(args, kwargs):

    multi = helpers.call_default(edit, 'multi', kwargs)

    return int(multi)


@_automatic(_edit_faller, False)
def edit(*,
         value = '',
         limit = None,
         funnel = None,
         indent = 4,
         trail = 2,
         callback = None,
         multi = False):

    (my, mx) = _edit_size()

    callback = _callback(callback)

    if multi:
        machine = _edit_machine_multi(trail, limit, funnel, indent, callback)
    else:
        machine = _edit_machine_single(limit, funnel, callback)

    _context.fall = int(multi)

    def prepare():
        machine.insert(value)

    return (machine, prepare)


def _select_size(limit, indent, prefix):

    (my, mx) = _context.size

    my = min(my, limit)

    mx -= max(indent, len(prefix))

    return (my, mx)


def _select_size_single(limit, indent, prefix):

    (my, mx) = _select_size(limit, indent, prefix)

    return (my, mx)


def _select_machine_single(limit,
                           options,
                           prefix,
                           indent,
                           funnel,
                           filter,
                           callback):

    (my, mx) = _select_size_single(limit, indent, prefix)

    select = machines.Select(
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


def _select_size_multi(limit, indent, prefix, unpin, pin):

    (my, mx) = _select_size(limit, indent, prefix)

    mx -= max(map(len, (unpin, pin)))

    return (my, mx)


def _select_machine_multi(limit,
                          options,
                          prefix,
                          indent,
                          funnel,
                          filter,
                          unpin,
                          pin,
                          indexes,
                          callback):

    (my, mx) = _select_size_multi(limit, indent, prefix, unpin, pin)

    select = machines.MultiSelect(
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


def _select_faller(args, kwargs):

    return 1


@_automatic(_select_faller, True)
def select(options,
           *,
           prefix = '> ',
           indent = None,
           funnel = None,
           filter = None,
           limit = 6,
           index = 0,
           unpin = '[ ] ',
           pin = '[X] ',
           indexes = (),
           callback = None,
           multi = False):

    if limit is None:
        limit = len(options)

    if indent is None:
        indent = len(prefix)

    if not filter:
        filter = _select_filter

    callback = _callback(callback)

    if multi:
        machine = _select_machine_multi(
            limit,
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
        machine = _select_machine_single(
            limit,
            options,
            prefix,
            indent,
            funnel,
            filter,
            callback
        )

    _context.fall = 0

    def prepare():
        machine.move(False, index)

    return (machine, prepare)
