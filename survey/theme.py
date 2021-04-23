
from . import helpers


__all__ = ('Auto', 'Palette', 'Symbol', 'Theme')


Auto = helpers.compat_namedtuple(
    'Auto',
    'pre_prompt hint_paint info_paint',
    defaults = (
        True,
        True,
        True
    )
)


Auto.__doc__ = ''


Palette = helpers.compat_namedtuple(
    'Palette',
    'note info done fail dark hint fade',
    defaults = (
        '\x1b[32m',
        '\x1b[36m',
        '\x1b[32m',
        '\x1b[31m',
        '\x1b[90m',
        '\x1b[90m',
        '\x1b[2m'
    )
)

Palette.__doc__ = ''


Symbol = helpers.compat_namedtuple(
    'Symbol',
    'note',
    defaults = (
        '? ',
    )
)

Symbol.__doc__ = ''


Theme = helpers.compat_namedtuple(
    'Theme',
    'auto palette symbol',
    defaults = (
        Auto(),
        Palette(),
        Symbol()
    )
)

Theme.__doc__ = ''
