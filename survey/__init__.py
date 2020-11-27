import itertools
import wrapio
import os
import functools

from . import api
from . import helpers
from . import utils

from . import _colors


__all__ = ('finish', 'update', 'input', 'password', 'accept', 'reject',
           'question', 'confirm', 'select', 'traverse', 'path')


def finish():

    """
    Stop listening for keypresses.
    """

    api.finish(False)


def update(value):

    """
    Update hint.
    """

    api.update(value)


_default_color = _colors.info


def _input(*args, **kwargs):

    result = api.edit(*args, **kwargs)

    return result


def input(*args, color = _default_color, erase = False, view = None, **kwargs):

    """
    input(*args, color=blue, erase=False, view=None, **kwargs)

    Await and return input.

    :param str color:
        Paints output.
    :param bool erase:
        Same as :func:`.api.edit`\'s ``full``.
    :param func view:
        Called with ``(result)``; should return ``list[str]`` to output.

    Other arguments are passed to :func:`.api.edit`.

    .. code-block:: py

        answer = survey.input('How old are you? ', '(age) ')
        print(f'You are {answer} years old!')
    """

    result = _input(*args, **kwargs)

    shows = None if view is None else view(result)

    api.respond(shows = shows, color = color, full = erase)

    return result


def password(*args, rune = '*', color = '\x1b[90m', **kwargs):

    """
    password(*args, rune='*', color=grey, **kwargs)

    Await and return input. Uses ``rune`` to replace keypresses.

    ``color`` (grey) and other arguments are passed to :func:`.input`.

    .. code-block:: py

        answer = survey.password('Secret: ')
        print(f'Singing in with {answer}...')
    """

    ofunnel = kwargs.pop('funnel', None)
    nfunnel = lambda _: rune

    funnel = helpers.combine_functions(ofunnel, nfunnel)

    def view(value):
        return (len(value) * rune,)

    result = input(*args, view = view, **kwargs, color = color, funnel = funnel)

    return result


def accept():

    """
    Respond with green.
    """

    api.respond(color = _colors.done)


def reject():

    """
    Respond with red.
    """

    api.respond(color = _colors.fail)


def question(*args, **kwargs):

    """
    Await and return input. Use :func:`.accept` or :func:`.reject` to respond.

    Other arguments are passed to :func:`.api.edit`.

    .. code-block:: py

        check = lambda answer: answer.isdigit()
        answer = survey.question('Solve 2+2: ', check = check)
        correct = int(answer) == 4
        (survey.accept if correct else survey.reject)()
    """

    return api.edit(*args, **kwargs)


def confirm(*args,
            default = None,
            sentiments = [
                ('n', 'no', '0', 'false', 'f'),
                ('y', 'yes', '1', 'true', 't')
            ],
            responses = ('No', 'Yes'),
            **kwargs):

    """
    confirm(*args, default=None, sentiments=[['n','no','0','false','f'],['y','yes','1','true','t']], responses=('No','Yes'), **kwargs)

    Await sentiment input and return respective :func:`.bool` value.

    :param list[set,set] sentiments:
        Containers of negative and positive options.
    :param list[str,str] responses:
        Negative and positive responses.
    :param bool default:
        Match empty responses to this.

    When ``hint`` is ommited, a suitable one takes its place.

    Other arguments except ``view``, ``limit`` and ``check`` are passed to
    :func:`.input`.

    .. code-block:: py

        result = survey.confirm('Proceed? ', default = True)
        print('Doing...' if result else 'Skipping...')
    """

    if not 'hint' in kwargs:
        template = helpers.paint('({0}/{1}) ', _colors.hint)
        color = kwargs.get('color', _default_color)
        kwargs['hint'] = utils.hint.confirm(template, default, color = color)

    index = None
    def check(value):
        if value:
            nonlocal index
            value = value.lower()
            for (index, sentiment) in enumerate(sentiments):
                if not value in sentiment:
                    continue
                break
            else:
                return False
        elif default is None:
            return False
        return True

    limit = max(map(len, itertools.chain.from_iterable(sentiments)))

    value = None
    def view(_):
        nonlocal value
        value = default if index is None else bool(index)
        response = responses[value]
        return (response,)

    input(
        *args,
        **kwargs,
        view = view,
        limit = limit,
        check = check
    )

    return value


def _select_hint_template_instructs(multi):

    values = ['filter: type', 'move: ↑↓']

    if multi:
        values.extend(('pick: → all: →→', 'unpick: ← all: ←←'))

    return values


def _select_hint_template(instructs):

    template = '{0} [' + ' | '.join(instructs) + ']'

    return template


def _select_hint(template, callback, external = True):

    template = helpers.paint(template, _colors.hint)

    (invoke, hint) = utils.hint.select(template, external = external)

    callback = helpers.succeed_functions(invoke, callback)

    return (callback, hint)


def _select(*args,
            color = _default_color,
            erase = False,
            **kwargs):

    if not 'hint' in kwargs:
        multi = kwargs.get('multi', False)
        instructs = _select_hint_template_instructs(multi)
        template = _select_hint_template(instructs)
        kwargs['hint'] = template

    template = kwargs['hint']
    if not template is None:
        callback = kwargs.get('callback')
        (invoke, hint) = _select_hint(template, callback)
        kwargs['callback'] = invoke
        kwargs['hint'] = hint

    result = api.select(*args, **kwargs, color = color)

    return result


def select(*args, color = _default_color, erase = False, view = None, **kwargs):

    """
    select(*args, color=blue, erase=False, view=None, **kwargs)

    Await and return input.

    :param str color:
        Paints output.
    :param bool erase:
        Same as :func:`.api.select`\'s ``full``.
    :param func view:
        Called with ``(result)``; should return ``list[str]`` to output.

    ``focus`` as ``color`` and other arguments are passed to
    :func:`.api.select`.

    When ``hint`` is ommited, a suitable one takes its place.

    Filter value is formatted on ``hint``\'s first placeholder (``{0}``).

    .. code-block:: py

        options = ('eat', 'sleep', 'code', 'repeat')
        index = survey.select(options, 'Do: ')

        options = ('bacon', 'lettuce', 'tomato', 'malted bread')
        indexes = survey.select(options, 'Use: ', multi = True)
    """

    try:
        kwargs['color'] = kwargs.pop('focus')
    except KeyError:
        pass

    result = _select(*args, **kwargs)

    shows = None if view is None else view(result)

    api.respond(shows = shows, color = color, full = erase)

    return result


def _traverse(path, show, able, next, *args, look = False, **kwargs):

    (options, displays) = next(path)

    track = wrapio.Track()

    wall = not len(path) > 1
    back = None

    @track.call
    def move_x(index, left, size):
        nonlocal back
        if left:
            if wall:
                raise api.Abort()
        else:
            option = options[index]
            if not able(path, option):
                raise api.Abort()
        back = left
        api.finish(True)

    try:
        template = kwargs.pop('hint')
    except KeyError:
        instructs = _select_hint_template_instructs(False)
        if any(able(path, option) for option in options):
            instructs.append('next: →')
        if not wall:
            instructs.append('back: ←')
        template = _select_hint_template(instructs)

    if show:
        showpath = show(path)
        template = template.format(showpath, '{0}')

    check = kwargs.pop('check', None)

    def subcheck(index):
        if back is None:
            option = options[index]
            return not check or check(path, option)
        return True

    index = _select(
        displays,
        *args,
        **kwargs,
        hint = template,
        check = subcheck,
        callback = track.invoke
    )

    if back is True:
        path.pop()
    else:
        option = options[index]
        path.append(option)
        if back is None:
            return path

    api.respond(shows = (), full = True)

    return _traverse(path, show, able, next, *args, check = check, **kwargs)


def traverse(initial, show, able, next, *args, **kwargs):

    """
    traverse(initial, show, able, next, *args, **kwargs)

    Cycle through proceedural pages of options.

    :param object initial:
        Used on ``next`` to determine options.
    :param func show:
        Called with ``(path)``; should return :class:`str` for hint formatting.
    :param func able:
        Called with ``(path, option)``; should return :class:`bool` for
        whether advancement is possible.
    :param func next:
        Called with ``(path)``; should return ``(options, displays)`` with
        latter used for drawing and former for selecting.
    :param bool look:
        Whether to assess if any option is advancable.

    ``show`` result is formatted on first placeholder (``{0}``) and filter value
    on second (``{1}``).

    ``check`` takes ``(path, option)``.
    """

    if 'multi' in kwargs:
        raise ValueError('multi makes no sense')

    view = kwargs.pop('view', None)
    color = kwargs.pop('color', _default_color)
    erase = kwargs.pop('erase', False)

    path = [initial]

    _traverse(path, show, able, next, *args, **kwargs)

    shows = None if view is None else view(path)

    api.respond(shows = shows, color = color, full = erase)

    return path


_path_units = ('f', '/', 'd')
_path_units = ('(' + unit + ')' for unit in _path_units)
_path_units = (helpers.paint(unit, _colors.hint) for unit in _path_units)
_path_units = (next(_path_units), (next(_path_units), next(_path_units)))

def path(directory,
         *args,
         units = _path_units,
         able = None,
         look = True,
         **kwargs):

    """
    path(directoy, *args, units=['f',['/','d']], able=None, look=True, **kwargs)

    Traverse a system directory until a file is selected.

    :param tuple[str,tuple[str,str]] units:
        ``f`` for non-dirs and ``/`` for empty dirs, ``d`` for dirs.
    :param func able:
        Called with ``(path)`` and should return :class:`bool` for whether to
        include in options.
    :param bool look:
        Works same as in :func:`.traverse`, but changed using memoization.

    ``check`` takes ``(path)``
    """

    def make(trail, *rest):
        return os.path.join(*trail, *rest)

    color = kwargs.get('color', _default_color)

    def show(trail):
        path = make(trail)
        path = helpers.paint(path, color)
        return path

    @functools.lru_cache(None)
    def contents(path):
        names = os.listdir(path)
        stick = lambda name: os.path.join(path, name)
        paths = map(stick, names)
        if able:
            try:
                (paths, names) = helpers.multifilter(able, paths, names)
            except ValueError:
                paths = names = ()
        else:
            paths = tuple(paths)
        return (names, paths)

    def able_(trail, part):
        path = make(trail, part)
        return os.path.isdir(path) and all(contents(path))

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
        check = kwargs['check']
    except KeyError:
        pass
    else:
        def subcheck(trail, part):
            path = make(trail, part)
            return check(path)
        kwargs['check'] = subcheck

    def view(trail):
        path = make(trail)
        return (path,)

    directory = os.path.join(directory, '') # ensure "/"

    trail = traverse(
        directory,
        show,
        able_,
        next,
        *args,
        **kwargs,
        look = look,
        view = view
    )

    result = make(trail)

    return result

del _path_units
