
"""
Functions that use :class:`~widget.Widget`\ s within a :class:`.stage.get` 
visual and respond with the formated result, before returning it upon submission.
"""

import os

from . import _helpers
from . import _colors
from . import _widgets
from . import _theme


__all__ = ('input', 'conceal', 'numeric', 'inquire', 'select', 'basket', 'datetime', 'form')


@_theme.add('routines.input.reply')
def _input_reply(widget,
                 result,
                 color = _colors.basic('cyan')):
    
    """
    |theme| :code:`'routines.input.reply'`
    """
    
    result = _helpers.paint_text(color, result)

    return result


@_theme.add('routines.input')
def _input(*args, 
           reply = _input_reply,
           **kwargs):
    
    """
    Use an :class:`~.widgets.Input` widget.

    All widget and :func:`~.widgets.start` arguments are valid.

    |theme| :code:`'routines.input'`

    .. image:: _static/images/routines.input-1.gif

    .. code-block:: python

        value = survey.routines.input('ping? ')
        print(f'Answered {value}.')

    .. image:: _static/images/routines.input-2.gif

    .. code-block:: python

        limit = 50
        def info(widget, name, info):
            result = widget.resolve().rstrip('\\n')
            remain = limit - len(result)
            if remain < 0:
                raise survey.widgets.Abort('no characters left')
            return str(remain)
        value = survey.routines.input('Limited Message: ', multi = True, info = info)
        print(f'Answered with {len(value)} characters.')
    """

    widget_kwargs_names = _helpers.get_function_args_names(_widgets.Input)
    widget_kwargs = _helpers.yank_dict(kwargs, widget_kwargs_names)
    widget = _widgets.Input(**widget_kwargs)

    multi_pre = widget_kwargs.get('multi', False)
    multi_aft = multi_pre

    result = _widgets.start(
        multi_pre, 
        multi_aft, 
        widget, 
        *args, 
        reply = reply, 
        **kwargs
    )

    return result


input = _input


@_theme.add('routines.numeric.reply')
def _numeric_reply(widget, 
                   result,
                   color = _colors.basic('cyan')):
    
    result = str(result)
    
    result = _helpers.paint_text(color, result)

    return result


@_theme.add('routines.numeric')
def _numeric(*args,
             reply = _numeric_reply,
             **kwargs):
    
    """
    Use an :class:`~.widgets.Count` widget.

    All widget and :func:`~.widgets.start` arguments are valid.

    |theme| :code:`'routines.numeric'`

    .. image:: _static/images/routines.numeric-1.gif

    .. code-block:: python

        value = survey.routines.numeric('Price: ')
        print(f'Answered {value}.')

    .. image:: _static/images/routines.numeric-2.gif

    .. code-block:: python

        value = survey.routines.numeric('Age: ', decimal = False)
        print(f'Answered {value}.')
    """

    widget_kwargs_names = _helpers.get_function_args_names(_widgets.Count)
    widget_kwargs = _helpers.yank_dict(kwargs, widget_kwargs_names)
    widget = _widgets.Count(**widget_kwargs)

    multi_pre = False
    multi_aft = multi_pre

    result = _widgets.start(
        multi_pre, 
        multi_aft, 
        widget, 
        *args, 
        reply = reply, 
        **kwargs
    )

    return result


numeric = _numeric


@_theme.add('routines.conceal.reply')
def _conceal_reply(widget, 
                   result, 
                   rune = '*', 
                   color = _colors.basic('black')):

    result = rune * len(result)

    result = _helpers.paint_text(color, result)

    return result


@_theme.add('routines.conceal')
def _conceal(*args,
             reply = _conceal_reply, 
             **kwargs):
    
    """
    Use an :class:`~.widgets.Conceal` widget.

    All widget and :func:`~.widgets.start` arguments are valid.

    |theme| :code:`'routines.conceal'`

    .. image:: _static/images/routines.conceal-1.gif

    .. code-block:: python
        
        value = survey.routines.conceal('Password: ')
        print(f'Answered {value}.')
    """

    widget_kwargs_names = _helpers.get_function_args_names(_widgets.Conceal)
    widget_kwargs = _helpers.yank_dict(kwargs, widget_kwargs_names)
    widget = _widgets.Conceal(**widget_kwargs)

    multi_pre = False
    multi_aft = multi_pre

    result = _widgets.start(
        multi_pre, 
        multi_aft, 
        widget, 
        *args, 
        reply = reply, 
        **kwargs
    )

    return result


conceal = _conceal


@_theme.add('routines.inquire.reply')
def _inquire_reply(widget, 
                   result, 
                   color = _colors.basic('cyan')):

    result = 'Yes' if result else 'No'

    result = _helpers.paint_text(color, result)

    return result


@_theme.add('routines.inquire')
def _inquire(*args, 
             default_color = _colors.basic('cyan'), 
             reply = _inquire_reply,
             **kwargs):
    
    """
    Use an :class:`~.widgets.Inquire` widget.

    :param options:
        The keys are used as :paramref:`.widgets.Inquire.options`. The resolving key's value is returned.
    :param default_color:
        Used in the default hint for signifying the default value. The default value must be part of :paramref:`.options`' values.

    All other widget and :func:`~.widgets.start` arguments are valid.

    |theme| :code:`'routines.inquire'`

    .. image:: _static/images/routines.inquire-1.gif

    .. code-block:: python

        value = survey.routines.inquire('Save? ', default = True)
        print(f'Answered {value}.')
    """

    widget_kwargs_names = _helpers.get_function_args_names(_widgets.Inquire)
    widget_kwargs = _helpers.yank_dict(kwargs, widget_kwargs_names)
    
    options = _helpers.get_function_arg_safe(_widgets.Inquire, 'options', widget_kwargs)
    default_value = _helpers.get_function_arg_safe(_widgets.Inquire, 'default', widget_kwargs)
    default_option = next((option for (option, value) in options.items() if value == default_value), default_value)

    widget_kwargs['default'] = default_option

    widget = _widgets.Inquire(**widget_kwargs)

    if not 'hint' in kwargs:
        hint_transform = lambda value: _helpers.paint_text(default_color, value.title())
        hint_segments = (hint_transform(option) if option == default_option else option for option in options)
        hint = kwargs['hint'] = '(' + '/'.join(hint_segments) + ')' + ' '

    multi_pre = False
    multi_aft = multi_pre

    value = _widgets.start(
        multi_pre, 
        multi_aft, 
        widget, 
        *args, 
        reply = reply, 
        **kwargs
    )

    return value


inquire = _inquire


def _select_hint_gen_instructions(widget):

    if not widget.mutate._search_score is None:
        yield 'filter: type'

    yield 'move: ↑↓'


def _select_hint(widget, name, info):

    instructions = _select_hint_gen_instructions(widget)

    value = '[' + ' | '.join(instructions) + ']'

    return value


@_theme.add('routines.select.reply')
def _select_reply(widget, 
                  index,
                  color = _colors.basic('cyan')):

    value = widget.mutate.cur_tile.resolve()
    
    value = _helpers.paint_text(color, value)

    return value


@_theme.add('routines.select')
def _select(*args, 
            reply = _select_reply, 
            **kwargs):
    
    """
    Use an :class:`~.widgets.Select` widget.

    The default hint shows available controls.

    All widget and :func:`~.widgets.start` arguments are valid.

    |theme| :code:`'routines.select'`

    .. image:: _static/images/routines.select-1.gif

    .. code-block:: python

        colors = ('red', 'green', 'blue', 'pink', 'silver', 'magenta')
        index = survey.routines.select('Pick a color: ', options = colors)
        print(f'Answered {index}.')

    .. image:: _static/images/routines.select-2.gif    

    .. code-block:: python

        names = map(''.join, itertools.combinations('AXBYCZ', 3))
        index = survey.routines.select('Favorite names? ',  options = names,  focus_mark = '~ ',  evade_color = survey.colors.basic('yellow'))
        print(f'Answered {index}.')
    """

    widget_kwargs_names = _helpers.get_function_args_names(_widgets.Select)
    widget_kwargs = _helpers.yank_dict(kwargs, widget_kwargs_names)
    widget = _widgets.Select(**widget_kwargs)

    kwargs.setdefault('hint', _select_hint)
    kwargs.setdefault('hint_parse', True)

    def info(widget, *args):
        mutate = widget.mutate
        lines = mutate.search_lines
        point = mutate.search_point
        return (lines, point)

    multi_pre = True
    multi_aft = False

    result = _widgets.start(
        multi_pre,
        multi_aft,
        widget,
        *args,
        info = info,
        info_parse = False,
        site = 'info',
        reply = reply,
        **kwargs
    )

    return result


select = _select


def _basket_hint_gen_instructions(widget):

    if not widget.mutate._search_score is None:
        yield 'filter: type'

    yield 'move: ↑↓'

    yield 'pick: → all: →→'
    yield 'unpick: ← all: ←←'


def _basket_hint(widget, name, info):

    instructions = _basket_hint_gen_instructions(widget)

    value = '[' + ' | '.join(instructions) + ']'

    return value


@_theme.add('routines.basket.reply')
def _basket_reply(widget, 
                  indexes, 
                  color = _colors.basic('cyan'), 
                  delimiter = ', '):
    
    size = len(widget.mutate.tiles)

    values = []
    for index in indexes:
        tile = widget.mutate.tiles[(index, 0)]
        tile_value_tile = tile.mutate.tiles[(0, 1)]
        tile_value_lines = tile_value_tile.mutate.lines
        tile_value = _helpers.join_lines(tile_value_lines)
        values.append(tile_value)

    values = (_helpers.paint_text(color, value) for value in values)

    value = delimiter.join(values)

    return value


@_theme.add('routines.basket')
def _basket(*args, 
            reply = _basket_reply, 
            **kwargs):
    
    """
    Use an :class:`~.widgets.Basket` widget.

    The default hint shows available controls.

    All widget and :func:`~.widgets.start` arguments are valid.

    |theme| :code:`'routines.basket'`

    .. image:: _static/images/routines.basket-1.gif

    .. code-block:: python

        days = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
        indexes = survey.routines.basket('Favourite days? ', options = days)
        print(f'Answered {indexes}.')

    .. image:: _static/images/routines.basket-2.gif

    .. code-block:: python

        names = tuple(map(''.join, itertools.combinations('AXBYCZ', 3)))
        def scout(spot):
            index = spot[0]
            name = names[index]
            return not 'C' in name
        index = survey.routines.basket('Favorite names? ',  options = names,  scout = scout,  evade_mark = '__',  focus_color = survey.colors.basic('magenta'), positive_mark = 'O ', negative_mark = 'X ',)
        print(f'Answered {index}.')
    """

    widget_kwargs_names = _helpers.get_function_args_names(_widgets.Basket)
    widget_kwargs = _helpers.yank_dict(kwargs, widget_kwargs_names)
    widget = _widgets.Basket(**widget_kwargs)

    kwargs.setdefault('hint', _basket_hint)
    kwargs.setdefault('hint_parse', True)

    def info(widget, *args):
        mutate = widget.mutate
        lines = mutate.search_lines
        point = mutate.search_point
        return (lines, point)

    multi_pre = True
    multi_aft = False

    result = _widgets.start(
        multi_pre, 
        multi_aft, 
        widget, 
        *args, 
        info = info,
        info_parse = False,
        site = 'info', 
        reply = reply, 
        **kwargs
    )

    return result


basket = _basket


@_theme.add('routines.datetime.reply')
def _datetime_reply(widget, 
                    result,
                    format = '%d/%m/%Y %H:%M',
                    color = _colors.basic('cyan')):

    result = result.strftime(format)
    
    result = _helpers.paint_text(color, result)

    return result


@_theme.add('routines.datetime')
def _datetime(*args,
             reply = _datetime_reply,
             **kwargs):
    
    """
    Use an :class:`~.widgets.DateTime` widget.

    All widget and :func:`~.widgets.start` arguments are valid.

    |theme| :code:`'routines.datetime'`

    .. image:: _static/images/routines.datetime-1.gif
    
    .. code-block:: python

        datetime = survey.routines.datetime('Schedule At: ')
        print(f'Answered {datetime}.')

    .. image:: _static/images/routines.datetime-2.gif
    
    .. code-block:: python

        datetime = survey.routines.datetime('Meeting Time: ', attrs = ('hour', 'minute'))
        print(f'Answered {datetime}.')
    """
    
    widget_kwargs_names = _helpers.get_function_args_names(_widgets.DateTime)
    widget_kwargs = _helpers.yank_dict(kwargs, widget_kwargs_names)
    widget = _widgets.DateTime(**widget_kwargs)

    multi_pre = False
    multi_aft = multi_pre

    result = _widgets.start(
        multi_pre, 
        multi_aft, 
        widget, 
        *args, 
        reply = reply, 
        **kwargs
    )

    return result


datetime = _datetime


_form_hint_gen_instructions_focus_extra = {
    _widgets.Select: _select_hint_gen_instructions,
    _widgets.Basket: _basket_hint_gen_instructions
}


def _form_hint_gen_instructions_focus(widget):

    sub_widget = widget.mutate.cur_tile.mutate.cur_tile

    try:
        extra = _form_hint_gen_instructions_focus_extra[sub_widget.__class__]
    except KeyError:
        pass
    else:
        yield from extra(sub_widget)

    yield 'back: submit'


def _form_hint_gen_instructions_blear(widget):

    yield from _select_hint_gen_instructions(widget)

    yield 'edit: <Tab>'


def _form_hint_gen_instructions(widget):

    if widget.focus:
        return _form_hint_gen_instructions_focus(widget)
    
    return _form_hint_gen_instructions_blear(widget)


_form_hint_gen_instructions_focus_extra[_widgets.Form] = _form_hint_gen_instructions


def _form_hint(widget, name, info):

    instructions = _form_hint_gen_instructions(widget)

    value = '[' + ' | '.join(dict.fromkeys(instructions)) + ']'

    return value


_form_reply_extra = {
    _widgets.Input: _input_reply,
    _widgets.Conceal: _input_reply,
    _widgets.Numeric: _numeric_reply,
    _widgets.Count: _numeric_reply,
    _widgets.Inquire: _inquire_reply,
    _widgets.Select: _select_reply,
    _widgets.Basket: _basket_reply,
    _widgets.DateTime: _datetime_reply,
}


@_theme.add('routines.form.reply')
def _form_reply(widget, 
                result,
                delimit = ': '):
    
    top_field_size = max(map(len, result))

    lines = []
    for widget in widget.mutate.tiles.values():
        field_widget = widget.mutate.tiles[(0, 0)]
        field = field_widget.resolve()
        value_widget = widget.mutate.tiles[(0, 1)]
        value = result[field]
        try:
            extra = _form_reply_extra[value_widget.__class__]
        except KeyError:
            value = str(value)
        else:
            value = extra(value_widget, value)
        lines.append(' ' * (top_field_size - len(field)) + field + delimit + value)

    result = '\n'.join(lines)

    return result


_form_reply_extra[_widgets.Form] = _form_reply


@_theme.add('routines.form')
def _form(*args,
          reply = _form_reply,
          **kwargs):
    
    """
    Use an :class:`~.widgets.Form` widget.

    The default hint shows available controls, including of focused widgets.

    All widget and :func:`~.widgets.start` arguments are valid.

    |theme| :code:`'routines.form'`

    .. image:: _static/images/routines.form-1.gif

    .. code-block:: python

        form = {
            'name': survey.widgets.Input(),
            'price': survey.widgets.Count(),
            'type': survey.widgets.Select(options = ('food', 'stationary', 'tobacco', 'literature'))
        }
        data = survey.routines.form('Item Data: ', form = form)
    """
    
    widget_kwargs_names = _helpers.get_function_args_names(_widgets.Form)
    widget_kwargs = _helpers.yank_dict(kwargs, widget_kwargs_names)
    widget = _widgets.Form(**widget_kwargs)

    kwargs.setdefault('hint', _form_hint)
    kwargs.setdefault('hint_parse', True)

    def info(widget, *args):
        mutate = widget.mutate
        lines = mutate.search_lines
        point = mutate.search_point
        return (lines, point)

    multi_pre = True
    multi_aft = True

    result = _widgets.start(
        multi_pre, 
        multi_aft, 
        widget, 
        *args, 
        reply = reply, 
        **kwargs
    )

    return result


form = _form
