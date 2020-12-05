import types
import contextlib
import inspect
import functools
import wrapio
import itertools
import os

from . import api
from . import theme
from . import helpers


__all__ = ('use', 'respond', 'finish', 'update', 'input', 'password', 'accept',
           'question', 'confirm', 'select', 'traverse', 'path')


_theme = theme.Theme()


_context = types.SimpleNamespace(
    theme = _theme
)


def _reset_theme():

    _context.theme = _theme


_theme_atomic = helpers.Atomic(leave = _reset_theme)


def use(theme):

    """
    use(theme)

    Signal for ``theme`` to be used within context.

    Subsequent calls within context are non-effective.
    """

    if _theme_atomic.open:
        _context.theme = theme

    return _theme_atomic


use.__returns_contextmanager__ = True # sphinx


def respond(*shows, color = None, erase = False, delimit = ', ', skip = False):

    """
    respond(*shows, color=None, erase=False, delimit=', ', skip=False)

    Clear info and hint and show results.

    :param list[str] shows:
        Stuff to show instead.
    :param str color:
        Used to paint each show. Defaults to ``theme.palette.info``.
    :param bool erase:
        Whether to also erase prompt.
    :param str delimit:
        Used to join shows together.
    :param bool skip:
        Whether to ignore internal results.
    """

    if color is None:
        color = _context.theme.palette.info

    def paint(show):
        show = helpers.paint(show, color)
        return show

    def format(shows):
        shows = map(paint, shows)
        return shows

    if not (shows or skip):
        shows = None

    api.respond(shows, format, erase, delimit)


def finish():

    """
    finish()

    Stop listening for keypresses. Result checking gets skipped.
    """

    api.finish(False)


def update(value):

    """
    update(value)

    Change info to ``value``.
    """

    value = _fix_info(value)

    api.update(value)


class Abort(api.Abort):

    """
    Triggers system's bell within callbacks.
    """

    __slots__ = ()


def _get_prompt(index, args, kwargs, key = 'prompt'):

    result = helpers.simulate_arg(
        args,
        kwargs,
        index = index,
        key = key,
        default = None,
        name = key
    )

    return result


def _fix_prompt(value):

    if _context.theme.auto.pre_prompt:
        symbol = _context.theme.symbol.note
        result = helpers.paint(symbol, _context.theme.palette.note)
    else:
        result = ''

    if not value is None:
        result += value

    return result


def _fix_info(value):

    result = ''

    if not value is None:
        if _context.theme.auto.info_paint:
            value = helpers.paint(value, _context.theme.palette.info)
        result += value

    return result


def _fix_hint(value):

    result = ''

    if not value is None:
        if _context.theme.auto.hint_paint:
            value = helpers.paint(value, _context.theme.palette.hint)
        result += value

    return result


def _visualizer_wrap(prompt_index,
                     function,
                     *args,
                     info = None,
                     hint = None,
                     auto = True,
                     **kwargs):

    args = list(args) # mutable

    visuals = []

    prompt = _get_prompt(prompt_index, args, kwargs)

    visuals = [prompt, info, hint]

    fixers = (_fix_prompt, _fix_info, _fix_hint)

    for (index, (visual, fixer)) in enumerate(zip(visuals, fixers)):
        visuals[index] = fixer(visual)

    result = function(*args, visuals = visuals, **kwargs)

    if auto:
        respond()

    return result


def _visualizer(prompt_index):

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            helpers.exclude_args(kwargs, 'visuals')
            return _visualizer_wrap(prompt_index, function, *args, **kwargs)
        return wrapper

    return decorator


@_visualizer(0)
def _input(*args, **kwargs):

    result = api.edit(*args, **kwargs)

    return result


def input(*args, **kwargs):

    """
    input(prompt=None, *, info=None, hint=None, multi=False, value='', check=None, limit=None, funnel=None, trail=2, callback=None, auto=True)

    Allow typing. Enter to submit. Await and return input from user.

    :param str prompt:
        Shown before input, static.
    :param str info:
        Shown after prompt, use :func:`update` to change.
    :param str hint:
        Shown after info, static, colored using ``theme.palette.hint``.
    :param bool multi:
        Whether to accept line breaks.
    :param str value:
        Creates the initial buffer.
    :param func check:
        Called with ``(result)``; returns :class:`bool` for whether to allow
        submission.
    :param int limit:
        Max allowed size of internal rune buffer.
    :param func funnel:
        Called with ``(rune)``; returns ``1``\-length class:`str` to
        replace.
    :param int trail:
        Amount of empty lines required to submit (**multi**).
    :param func callback:
        Called with ``(name, result, *args)`` on keypress events.
    :param bool auto:
        Whether to immediately :func:`respond` after submission.
    """

    result = _input(*args, **kwargs)

    return result


def password(*args, rune = '*', color = None, **kwargs):

    """
    password(*args, rune='*', color=None, **kwargs)

    Conseal typing. Responds immediately.

    :param str rune:
        Used to substitute runes.
    :param str color:
        Used for painting response.

    Arguments except ``auto`` and ``funnel`` are passed to :func:`.input`.
    """

    helpers.exclude_args(kwargs, 'auto', 'funnel')

    def funnel(value):
        result = rune
        return result

    result = input(*args, auto = False, funnel = funnel, **kwargs)

    show = rune * len(result)

    if not color:
        color = _context.theme.palette.dark

    respond(show, color = color)

    return result


def accept(correct, *args, **kwargs):

    """
    Respond with ``theme.palette.done`` if ``correct`` is ``True``, and
    ``theme.palette.fail`` otherwise.

    Arguments except ``color`` are passed to :func:`.respond`.
    """

    helpers.exclude_args(kwargs, 'color')

    color = (
        _context.theme.palette.done
        if correct
        else _context.theme.palette.fail
    )

    respond(*args, color = color, **kwargs)


def question(*args, **kwargs):

    """
    Await and return input. Use :func:`.accept` to respond.

    Arguments except ``auto`` are passed to :func:`.input`.
    """

    helpers.exclude_args(kwargs, 'auto')

    return input(*args, auto = False, **kwargs)


def _confirm_hint_option(options):

    try:
        result = options[0]
    except TypeError:
        key = lambda option: len(option)
        options = sorted(options, key = key)
        key = lambda option: not option.isdigit()
        options = sorted(options, key = key, reverse = True)
        result = _confirm_hint_option(options)

    return result


def _confirm_hint(default, sentiments, template = '({0}/{1}) '):

    options = list(map(_confirm_hint_option, sentiments))

    if not default is None:
        index = int(default)
        option = options[index]
        option = option.upper()
        if _context.theme.auto.hint_paint:
            option = helpers.paint(option, _context.theme.palette.info)
        options[index] = option

    if default is True:
        options = reversed(options)

    result = template.format(*options)

    return result


def confirm(*args,
            default = None,
            sentiments = (
                ('n', 'no', '0', 'false', 'f'),
                ('y', 'yes', '1', 'true', 't')
            ),
            responses = ('No', 'Yes'),
            color = None,
            **kwargs):

    """
    confirm(*args, default=None, sentiments=[['n','no','0','false','f'],['y','yes','1','true','t']], responses=['No','Yes'], color=blue, **kwargs)

    Await sentiment input and return respective :func:`.bool` value.

    :param bool default:
        Match empty responses to this.
    :param list[set,set] sentiments:
        Negative and positive options.
    :param list[str,str] responses:
        Negative and positive responses.
    :param str color:
        Used for painting response.

    When ``hint`` is ommited, a suitable one takes its place.

    Arguments except ``auto``, ``limit`` and ``check`` are passed to
    :func:`.input`.
    """

    helpers.exclude_args(kwargs, 'auto', 'limit', 'check')

    limit = max(map(len, itertools.chain.from_iterable(sentiments)))

    def _is_default(value):
        result = not (value or default is None)
        return result

    index = None

    def _is_option(value):
        nonlocal index
        value = value.lower()
        for (index, options) in enumerate(sentiments):
            if not value in options:
                continue
            break
        else:
            return False
        return True

    def check(value):
        result = _is_default(value) or _is_option(value)
        return result

    if not 'hint' in kwargs:
        hint = _confirm_hint(default, sentiments)
        kwargs['hint'] = hint

    input(*args, auto = False, check = check, limit = limit, **kwargs)

    result = default if index is None else bool(index)

    index = int(result)
    response = responses[index]

    respond(response, color = color)

    return result


def _select_info(template, default = ''):

    def format(argument):
        if not argument:
            argument = default
        result = template.format(argument)
        return result

    track = wrapio.Track()

    @track.call
    def filter(index, argument):
        info = format(argument)
        update(info)

    callback = track.invoke

    result = format('')

    return (callback, result)


def _select_hint(multi,
                 basic_instructs = ('filter: type', 'move: ↑↓'),
                 multi_instructs = ('pick: → all: →→',  'unpick: ← all: ←←'),
                 extra_instructs = (),
                 delimit = ' | ',
                 template = '[{0}]'):

    instructs = []
    instructs.extend(basic_instructs)
    if multi:
        instructs.extend(multi_instructs)
    instructs.extend(extra_instructs)

    manual = delimit.join(instructs)

    result = template.format(manual)

    return result


@_visualizer(1)
def _select(*args, **kwargs):

    result = api.select(*args, **kwargs)

    return result


def select(*args, **kwargs):

    """
    select(options, prompt=None, *, info=None, hint=None, color=None, multi=False, check=None, prefix='> ', indent=None, funnel=None, filter=None, limit=6, unpin='[ ] ', pin='[X] ', indexes=[], callback=None, auto=True)

    Draw a menu of options. Traverse using **↑** and **↓** keys. Type to filter.
    Enter to submit. Await and return index(es) of option(s).

    :param list[str] options:
        Values shown for selection.
    :param str prompt:
        Shown before input, static.
    :param str info:
        Shown after prompt, use :func:`update` to change. When ommited, defaults
        to an updating value of ``filter`` painted using ``theme.palette.info``.
    :param str hint:
        Shown after info, static, colored using ``theme.palette.hint``.
    :param str color:
        Used to paint focused options. When omitted, defaults to
        ``theme.palette.info``.
    :param bool multi:
        Whether to allow multiple selections using **←** and **→** keys.
    :param func check:
        Called with ``(index)`` (or ``(indexes)`` if ``multi``); returns
        :class:`bool` for whether to allow submission.
    :param str prefix:
        Drawn before focused option.
    :param int indent:
        Empty space before each option. Defaults to ``len(prefix)``.
    :param func funnel:
        Called with ``(index, option)`` when focused; returns :class:`str`.
    :param func filter:
        Called with ``(((index, option), ...), argument)`` when typing; yields
        ``(index, option)``\s to be shown. Defaults to internal routine.
    :param int limit:
        Maximum amount of options displayed at any point.
    :param int index:
        Index of option to focus upon initial draw.
    :param str unpin:
        Indicator for un-selected options (**multi**).
    :param str pin:
        Indicator for selected options (**multi**).
    :param list[int] indexes:
        Indexes of options to pre-select upon initial draw (**multi**).
    :param func callback:
        Used with ``(name, *args)`` for listening to keypress events.
    :param bool auto:
        Whether to immediately :func:`respond` after submission.

    Event names are followed by current result, and then arguments.
    """

    color = kwargs.pop('color', _context.theme.palette.info)

    if not color is None:
        funnel = kwargs.get('funnel')
        def subfunnel(index, option):
            result = helpers.paint(option, color)
            return result
        funnel = helpers.combine_functions(funnel, subfunnel, index = 1)
        kwargs['funnel'] = funnel

    callbacks = [
        helpers.call_default(api.select, 'callback', kwargs)
    ]

    template = kwargs.get('info', '{0} ')
    (callback, info) = _select_info(template)
    callbacks.append(callback)
    kwargs['info'] = info

    multi = helpers.call_default(api.select, 'multi', kwargs)

    if not 'hint' in kwargs:
        hint = _select_hint(multi)
        kwargs['hint'] = hint

    kwargs['callback'] = helpers.succeed_functions(*reversed(callbacks))

    result = _select(*args, **kwargs)

    return result


def _traverse_hint(next,
                   back,
                   jump,
                   next_instruct = 'next: →',
                   back_instruct = 'back: ←',
                   jump_instruct = 'jump: ⇥',
                   extra_instructs = ()):

    pairs = (
        (next, next_instruct),
        (back, back_instruct),
        (jump, jump_instruct)
    )

    instructs = []
    for (check, instruct) in pairs:
        if not check:
            continue
        instructs.append(instruct)

    instructs.extend(extra_instructs)

    result = _select_hint(False, extra_instructs = instructs)

    return result


def _traverse(trail, able, next, *args, show = None, jump = None, **kwargs):

    subargs = tuple(args)
    subkwargs = kwargs.copy()

    callbacks = [
        helpers.call_default(api.select, 'callback', kwargs)
    ]

    (options, displays) = next(trail)

    able_next = any(able(trail, option) for option in options)

    track = wrapio.Track()

    wall = not len(trail) > 1
    back = None

    able_back = not wall

    def _move_x(left, index):
        nonlocal back
        if left:
            allowed = able_back
        else:
            option = options[index]
            allowed = able(trail, option)
        if not allowed:
            raise Abort()
        back = left
        finish()

    @track.call
    def move_x(index, left, size):
        _move_x(left, index)

    if jump:
        (jump_index, info_default) = jump(trail, options)
    else:
        (jump_index, info_default) = (None, None)

    if info_default is None:
        info_default = ''

    able_jump = not jump_index is None

    force = False

    def _tab():
        nonlocal force
        if not able_jump:
            raise Abort()
        _move_x(False, jump_index)
        force = True

    @track.call
    def tab(index):
        _tab()

    if show:
        info_show = show(trail)
        template = kwargs.get('info', '{1}{0} ')
        template = template.format('{0}', info_show)
        if _context.theme.auto.info_paint:
            info_default = helpers.paint(
                info_default,
                _context.theme.palette.fade
            )
        (callback, info) = _select_info(template, default = info_default)
        callbacks.append(callback)
        kwargs['info'] = info

    if not 'hint' in kwargs:
        hint = _traverse_hint(able_next, able_back, able_jump)
        kwargs['hint'] = hint

    try:
        indexer = kwargs['index']
    except KeyError:
        if able_jump:
            kwargs['index'] = jump_index
    else:
        kwargs['index'] = indexer(trail, options)

    check = kwargs.get('check')
    if check:
        def subcheck(index):
            if back is None:
                option = options[index]
                return check(trail, option)
            return True
        kwargs['check'] = subcheck

    callbacks.append(track.invoke)

    kwargs['callback'] = helpers.succeed_functions(*reversed(callbacks))

    index = select(displays, *args, auto = False, **kwargs)

    if back is True:
        trail.pop()
    else:
        if force:
            index = jump_index
        option = options[index]
        trail.append(option)
        if back is None and not force:
            return trail

    respond(erase = True, skip = True)

    result = _traverse(
        trail,
        able,
        next,
        *subargs,
        show = show,
        jump = jump,
        **subkwargs
    )

    return result


def traverse(initial, *args, **kwargs):

    """
    traverse(initial, able, next, *args, show=None, jump=None, **kwargs)

    Cycle through proceedural pages of options.

    :param object initial:
        Used on ``next`` to determine options.
    :param func able:
        Called with ``(trail, option)``; returns :class:`bool` for whether
        advancement is possible.
    :param func next:
        Called with ``(trail)``; returns ``(options, displays)`` with former
        used for selecting and latter for drawing.
    :param func show:
        Called with ``(trail)``; returns ``(path)`` for info formatting.
    :param func jump:
        Called with ``(trail)``; returns ``(index, display)`` with former
        used as forceful select upon **⇥** and latter for info formatting. Both
        values can be ``None`` to disable.

    Arguments except ``multi`` are passed to :func:`.traverse`.

    .. note::

        - ``check`` takes ``(trail, option)``.
        - ``index`` is func taking ``(trail, options)`` and should return :class:`int`.
    """

    helpers.exclude_args(kwargs, 'multi')

    trail = [initial]

    try:
        auto = kwargs.pop('auto')
    except KeyError:
        auto = helpers.call_default(_visualizer_wrap, 'auto', kwargs)

    _traverse(trail, *args, **kwargs)

    if auto:
        respond()

    return trail


def _path_units(values = ('f', '/', 'd')):

    values = ('(' + value + ')' for value in values)

    if _context.theme.auto.hint_paint:
        paint = lambda value: helpers.paint(value, _context.theme.palette.hint)
        values = map(paint, values)

    generate = iter(values)

    result = (next(generate), (next(generate), next(generate)))

    return result


def path(directory, *args, units = None, allow = None, **kwargs):

    """
    path(directoy, *args, units=['(f)','(/)','(d)'], able=None, **kwargs)

    Traverse a system directory until a file is selected.

    :param tuple[str,str,str] units:
        ``f`` for non-dirs and ``/`` for empty dirs, ``d`` for dirs.
    :param func able:
        Called with ``(path)`` and should return :class:`bool` for whether to
        include in options.

    Other arguments are passed to :func:`.traverse`.

    .. note::

        - ``check`` takes ``(path)``
        - ``index`` takes ``(path, options)``
    """

    def make(trail, *rest):
        return os.path.join(*trail, *rest)

    def show(trail):
        path = make(trail)
        path = os.path.join(path, '')
        if _context.theme.auto.info_paint:
            path = helpers.paint(path, _context.theme.palette.info)
        return path

    @functools.lru_cache(None)
    def contents(path):
        names = os.listdir(path)
        names = sorted(names) # qof
        stick = lambda name: os.path.join(path, name)
        paths = map(stick, names)
        if allow:
            try:
                (paths, names) = helpers.multifilter(allow, paths, names)
            except ValueError:
                paths = names = ()
        else:
            paths = tuple(paths)
        return (names, paths)

    def able(trail, part):
        path = make(trail, part)
        return os.path.isdir(path) and all(contents(path))

    if not units:
        units = _path_units()

    def next(trail):
        path = make(trail)
        (names, paths) = contents(path)
        limit = max(map(len, names))
        shows = []
        for (name, path) in zip(names, paths):
            pred = os.path.isdir(path)
            unit = units[pred]
            if pred:
                pred = all(contents(path))
                unit = unit[pred]
            push = limit - len(name) + 1
            show = name + ' ' * push + unit
            shows.append(show)
        return (names, shows)

    try:
        subindexer = kwargs['index']
    except KeyError:
        pass
    else:
        def indexer(trail, parts):
            path = make(trail)
            result = subindexer(path, parts)
            return result
        kwargs['index'] = indexer

    try:
        subcheck = kwargs['check']
    except KeyError:
        pass
    else:
        def check(trail, part):
            path = make(trail, part)
            result = subcheck(path)
            return result
        kwargs['check'] = check

    directory = os.path.join(directory, '') # ensure "/"

    try:
        auto = kwargs.pop('auto')
    except KeyError:
        auto = helpers.call_default(_visualizer_wrap, 'auto', kwargs)

    trail = traverse(
        directory,
        able,
        next,
        *args,
        show = show,
        auto = False,
        **kwargs
    )

    result = make(trail)


    if auto:
        respond(result)

    return result
