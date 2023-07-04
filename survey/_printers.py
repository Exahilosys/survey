
"""
Functions that print to the console with optional sentiment using marks.
"""

import typing
import os

from . import _constants
from . import _helpers
from . import _system
from . import _colors
from . import _theme


__all__ = ('text', 'info', 'done', 'fail')


_type_text_sep = str
_type_text_end = str
_type_text_re  = bool


def _text(*values, 
          sep: _type_text_sep = ' ', 
          end: _type_text_end = _constants.linesep, 
          re : _type_text_re  = False):

    """
    Print a plain value. Works similar to :func:`print`.

    :param values:
        Used to create the final value by mapping all with :func:`str` and concatenating with :paramref:`.text.sep`.
    :param end:
        Appended to the end of the final value.
    :param re:
        Whether to return the cursor to the last saved position before printing.
    """

    def sketch():
        value = sep.join(map(str, values)) + end
        lines = _helpers.split_lines(value)
        point = None
        return (lines, point)

    _system.screen.print(sketch, re)


text = _text


def _annotate(mark_color, mark, values, **kwargs):

    if not mark_color is None:
        mark = _helpers.paint_text(mark_color, mark)

    _text(mark, *values, **kwargs)


_type_info_mark       = str
_type_info_mark_color = str


@_theme.add('printers.info')
def _info(*values,
          mark      : _type_info_mark       = '!', 
          mark_color: _type_info_mark_color = _colors.basic('cyan'),
          **kwargs):

    """
    Print a value denoting information.

    :param values:
        Same as :paramref:`.text.value`.
    :param mark:
        Prepended to the final value.
    :param mark_color:
        Used to color :paramref:`.info.mark` with.

    Additional arguments are passed to :func:`.text`.

    |theme| :code:`printers.info`.

    .. image:: /_static/images/printers.info-1.png
    """

    _annotate(mark_color, mark, values, **kwargs)


info = _info


_type_done_mark       = str
_type_done_mark_color = str


@_theme.add('printers.done')
def _done(*values,
          mark      : _type_done_mark       = '!' if os.name == 'nt' else '✔', 
          mark_color: _type_done_mark_color = _colors.basic('green'),
          **kwargs):

    """
    Print a value denoting success.

    :param values:
        Same as :paramref:`.text.value`.
    :param mark:
        Prepended to the final value.
    :param mark_color:
        Used to color :paramref:`.info.mark` with.

    Additional arguments are passed to :func:`.text`.

    |theme| :code:`printers.done`.

    .. image:: /_static/images/printers.done-1.png
    """

    _annotate(mark_color, mark, values, **kwargs)


done = _done


_type_fail_mark       = str
_type_fail_mark_color = str


@_theme.add('printers.fail')
def _fail(*values,
          mark      : _type_fail_mark       = '!' if os.name == 'nt' else '✘', 
          mark_color: _type_fail_mark_color = _colors.basic('red'),
          **kwargs):

    """
    Print a value denoting failure.

    :param values:
        Same as :paramref:`.text.value`.
    :param mark:
        Prepended to the final value.
    :param mark_color:
        Used to color :paramref:`.info.mark` with.

    Additional arguments are passed to :func:`.text`.

    |theme| :code:`printers.fail`.

    .. image:: /_static/images/printers.fail-1.png
    """

    _annotate(mark_color, mark, values, **kwargs)


fail = _fail
