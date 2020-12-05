import collections


__all__ = ('Auto', 'Palette', 'Symbol', 'Theme')


Auto = collections.namedtuple(
    'Auto',
    'pre_prompt hint_paint info_paint',
    defaults = (
        True,
        True,
        True
    )
)


Auto.__doc__ = ''


Palette = collections.namedtuple(
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


Symbol = collections.namedtuple(
    'Symbol',
    'note',
    defaults = (
        '? ',
    )
)

Symbol.__doc__ = ''


Theme = collections.namedtuple(
    'Theme',
    'auto palette symbol',
    defaults = (
        Auto(),
        Palette(),
        Symbol()
    )
)

Theme.__doc__ = ''
