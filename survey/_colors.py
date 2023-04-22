
"""
Utilities for dealing with `ANSI Colors <https://en.wikipedia.org/wiki/ANSI_escape_code#Colors>`_.
"""

from . import _core
from . import _helpers


__all__ = ('style', 'basic', 'standard', 'full')


def _get(*args):

    return _core.ansi.get_control('m', *args)


_style_info = {
               'reset': 0,
              'strong': 1,
               'faint': 2,
              'italic': 3,
           'underline': 4,
          'slow_blink': 5,
         'rapid_blink': 6,
             'reverse': 7,
             'conceal': 8,
              'strike': 9,
    'underline_double': 21,
     'reset_intensity': 22,
        'reset_italic': 23,
     'reset_underline': 24,
         'reset_blink': 25,
       'reset_reverse': 27,
       'reset_conceal': 28,
        'reset_strike': 29,
      'reset_fg_color': 39,
      'reset_bg_color': 48
}


_style_info_doc = ', '.join(map('``{0}``'.format, _style_info))


def style(name: str) -> str:

    part = _style_info[name]

    value = _get(part)

    return _helpers.IdentifiableSGR(value, sl = name)

style.__doc__ = (
    """
    Get an ansi style by name.

    .. code-block:: python

        faint = colors.style('faint')

    The following styles are available: {0}
    """.format(_style_info_doc)
)


_color_bit4_info = {
      'black': ((30, 40), (90, 100)),
        'red': ((31, 41), (91, 101)),
      'green': ((32, 42), (92, 102)),
     'yellow': ((33, 43), (93, 103)),
       'blue': ((34, 44), (94, 104)),
    'magenta': ((35, 45), (95, 105)),
       'cyan': ((36, 46), (96, 106)),
      'white': ((37, 47), (97, 107)),
}


_color_bit4_light_indexes = {
    'dark': 0,
    'lite': 1
}


_color_bit4_layer_indexes = {
    'fg': 0,
    'bg': 1
}


def _color_bit4_resolve(path):

    (name, *rest) = path.split('.')

    info = {'name': name}

    part = _color_bit4_info[name]

    for (key, indexes) in (('light', _color_bit4_light_indexes), ('layer', _color_bit4_layer_indexes)):
        try:
            (name, *rest) = rest
        except ValueError:
            break
        info[key] = name
        index = indexes[name]
        part = part[index]

    return (part, info)


_color_default_light = 'lite'


def _color_bit4_get(fg_path, bg_path):

    default_light = _color_default_light

    store = []
    for (part, default_layer) in ((fg_path, 'fg'), (bg_path, 'bg')):
        if part is None:
            continue
        name, *rest = part.split('.')
        try:
            light, *rest = rest
        except ValueError:
            light = default_light
        light_index = _color_bit4_light_indexes[light]
        try:
            layer, *rest = rest
        except ValueError:
            layer = default_layer
        layer_index = _color_bit4_layer_indexes[layer]
        value = _color_bit4_info[name][light_index][layer_index]
        store.append(value)

    return _get(*store)


def basic(fg: str = None, bg: str = None) -> str:

    """
    Get a basic ansi color by path (`4 bit docs <https://en.wikipedia.org/wiki/ANSI_escape_code#3-bit_and_4-bit>`_). 

    :param fg:
        The foreground color.
    :param bg:
        The background color.

    .. code-block:: python

        fg_lite_blue = basic('blue.lite')
        fg_dark_green = basic('green.dark')
        bg_lite_yellow = basic(bg = 'yellow') # .lite can be ommited
        bg_dark_red_fg_dark_cyan = basic(fg = 'red.dark', bg = 'cyan.dark')
    """

    value = _color_bit4_get(fg, bg)
    
    return _helpers.IdentifiableSGR(value, fg = fg, bg = bg)


_color_default_layer = 'fg'


_color_bit8_info = {
    'fg': (38, 5),
    'bg': (48, 5)
}


def _color_bit8_info_get(layer, part):

    args = _color_bit8_info[layer]

    return _get(*args, part)


def standard(part: str, /, layer: str = _color_default_layer) -> str:

    """
    Get a standard ansi color by value (`8 bit docs <https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit>`_).

    :param part:
        The color in ``[0, 255]`` range.
    :param layer:
        Whether it's foreground (:code:`'fg'`) or background (:code:`'bg'`). 

    .. code-block:: python

        fg_blue = standard(4)
        fg_pink = standard(225)
        bg_cyan = standard(6, 'bg')
    """
    
    return _color_bit8_info_get(layer, part)


_color_bit24_info = {
    'fg': (38, 2),
    'bg': (48, 2)
}


def _color_bit24_get(layer, part_r, part_g, part_b):

    args = _color_bit24_info[layer]

    return _get(*args, part_r, part_g, part_b)


def full(part_r: int, part_g: int, part_b: int, /, layer: str = _color_default_layer) -> str:

    """
    Get a full rgb ansi color by the respective values (`224 bit docs <https://en.wikipedia.org/wiki/ANSI_escape_code#24-bit>`_).

    :param part_r:
        The red component.
    :param part_g:
        The green component.
    :param part_b:
        The blue component.
    :parma layer:
        Whether it's foreground (:code:`'fg'`) or background (:code:`'bg'`). 

    .. code-block:: python

        fg_steel = full(113, 121, 126)
        bg_brick = fill(170, 74, 68, 'bg')
    """
    
    return _color_bit24_get(layer, part_r, part_g, part_b)