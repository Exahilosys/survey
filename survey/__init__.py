import types
import itertools

from . import api
from . import helpers


__all__ = ('update', 'edit', 'input', 'password', 'accept', 'reject',
           'question', 'confirm', 'select')


_assets = types.SimpleNamespace(
    colors = types.SimpleNamespace(
        info = '\x1b[38;5;6m',
        done = '\x1b[38;5;10m',
        fail = '\x1b[38;5;9m',
        hint = '\x1b[37m',
        null = helpers.paint.null
    )
)


def update(value):

    """
    Update the hint.
    """

    api.update(value)


def edit(*args, color = None, **kwargs):

    """
    Same as :func:`api.edit`, except responds immediately using ``color``.

    Other arguments are passed to :func:`edit`.
    """

    result = api.edit(*args, **kwargs)

    api.respond(color = color)

    return result


def input(*args, color = _assets.colors.info, **kwargs):

    """
    Same as :func:`edit`, but with a default color.

    Other arguments are passed to :func:`edit`.

    .. code-block:: py

        answer = survey.input('How old are you? ', '(age) ')
        print(f'You are {answer} years old!')
    """

    return edit(*args, color = color, **kwargs)


def password(*args, rune = '*', color = '\x1b[90m', **kwargs):

    """
    Await and return input. Uses ``rune`` to replace keypresses. Color is grey.

    Other arguments are passed to :func:`edit`.

    .. code-block:: py

        answer = survey.password('Secret: ')
        print(f'Singing in with {answer}...')
    """

    ofunnel = kwargs.pop('funnel', None)
    nfunnel = lambda _: rune

    funnel = helpers.combine_functions(ofunnel, nfunnel)

    def view(value):
        return (len(value) * rune,)

    return edit(*args, view = view, color = color, **kwargs, funnel = funnel)


def accept():

    """
    Respond with green.
    """

    api.respond(color = _assets.colors.done)


def reject():

    """
    Respond with red.
    """

    api.respond(color = _assets.colors.fail)


def question(*args, **kwargs):

    """
    Await and return input. Use ``accept`` or ``reject`` to respond with color.

    This is an alias for :func:`api.edit`.

    .. code-block:: py

        check = lambda answer: answer.isdigit()
        answer = survey.question('Solve 2+2: ', check = check)
        correct = int(answer) == 4
        (survey.accept if correct else survey.reject)()
    """

    return api.edit(*args, **kwargs)


def _confirm_hint(default = None, options = ('n', 'y'), title = True):

    result = f'{_assets.colors.hint}('

    options = list(options)

    if not default is None:
        option = options[default]
        if title:
            option = option.title()
        options[default] = f'{_assets.colors.info}{option}{_assets.colors.hint}'
        if default:
            options = reversed(options)

    result += '/'.join(options) + f'){_assets.colors.null} '

    return result


def confirm(*args,
            sentiments = [
                ('n', 'no', '0', 'false', 'f'),
                ('y', 'yes', '1', 'true', 't')
            ],
            responses = ('No', 'Yes'),
            default = None,
            color = _assets.colors.info,
            **kwargs):

    """
    Await sentiment input and return respective :func:`bool` value.

    :param list[set,set] sentiments:
        Containers of negative and positive options.
    :param list[str,str] responses:
        Negative and positive responses.
    :param bool default:
        Match empty responses to this.

    When ``hint`` is ommited, a suitable one takes its place.

    Other arguments except ``limit`` and ``check`` are passed to :func:`input`.

    .. code-block:: py

        result = survey.confirm('Proceed? ', default = True)
        print('Doing...' if result else 'Skipping...')
    """

    if not 'hint' in kwargs:
        kwargs['hint'] = _confirm_hint(default)

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

    input(*args, view = view, **kwargs, limit = limit, check = check)

    return value


def _select_hint(multi, instruct = 'type'):

    instructions = ['filter: {0}', 'move: ↑↓']
    if multi:
        instructions.extend(('pick: → all: →→', 'unpick: ← all: ←←'))

    template = ' | '.join(instructions)
    template = f'{_assets.colors.hint}[{template}]{_assets.colors.null}'

    def callback(event, result, *args):
        if event == 'filter':
            (value,) = args
            if value:
                show = _assets.colors.info + value + _assets.colors.hint
            else:
                show = instruct
            hint = template.format(show)
            update(hint)

    hint = template.format(instruct)

    return (callback, hint)


def select(*args,
           color = _assets.colors.info,
           focus = _assets.colors.info,
           **kwargs):

    """
    Same as :func:`api.select`, except responds immediately using ``color``.

    When ``hint`` is ommited, a suitable one takes its place.

    Other arguments are passed to :func:`api.select`, with ``focus`` being its
    ``color``.

    .. code-block:: py

        options = ('eat', 'sleep', 'code', 'repeat')
        index = survey.select(options, 'Do: ')

        options = ('bacon', 'lettuce', 'tomato', 'malted bread')
        indexes = survey.select(options, 'Use: ', multi = True)
    """

    if not 'hint' in kwargs:
        multi = kwargs.get('multi', False)
        (callback, hint) = _select_hint(multi)
        callbacks = [callback]
        try:
            callback = kwargs['callback']
        except KeyError:
            pass
        else:
            callbacks.append(callback)
        def callback(*args, **kwargs):
            for callback in callbacks:
                callback(*args, **kwargs)
        kwargs['callback'] = callback
        kwargs['hint'] = hint

    result = api.select(*args, **kwargs, color = focus)

    api.respond(color = color)

    return result
