
"""
Themeing is essentially changing the default values for elligible callables.

Look for the "|theme|" sections to see which functions are subject to themeing. 
"""

import functools
import contextlib


__all__ = ('use', 'get')


_store = []

_store_default = {}


@contextlib.contextmanager
def _use(theme: dict):

    """
    Use the theme where applicable. This overrides any subsequent themes.

    A theme is a collection of default arguments for specified functions.

    .. code-block:: python

        with theme.use({'printers.info': {'mark_color': colors.basic('magenta')}}):
            with theme.use({'printers.done': {'mark_color': colors.basic('yellow')}}):
                survey.printers.info('example')
                survey.printers.done('example')

    On the above example, only the marker of ``info`` will be painted magenta.
    """

    _store.append(theme)

    yield

    _store.pop()


use = _use


def _get():

    """
    Get the current theme, with all subsequent values attached to it.
    """

    try:
        return _store[0]
    except IndexError:
        return _store_default


get = _get


def add(name: str):

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            theme = _get()
            try:
                defaults = theme[name]
            except KeyError:
                pass
            else:
                kwargs = defaults | kwargs
            return function(*args, **kwargs)
        return wrapper

    return decorator