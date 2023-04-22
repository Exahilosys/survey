
"""
General utilities.
"""

from . import _helpers


__all__ = ('paint',)


def paint(color: str, 
          value: str,
          *,
          force: bool = False) -> str:

    """
    Get the colored version of the value.
    """

    if force:
        value = _helpers.SGR.clean(value)

    return _helpers.paint_text(color, value)


def chain_funnels(*funnels):

    return _helpers.chain_functions(*funnels)


def split_lines(value):

    return _helpers.split_lines(value)


def join_lines(value):

    return _helpers.join_lines(value)