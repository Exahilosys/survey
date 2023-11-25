
"""
Functions that can be used for changing the way data appears upon printing.

Specifically, they are meant to be passed to :paramref:`~.visuals.Visual.funnel_enter` or :paramref:`~.visuals.Visual.funnel_leave`.
All ``text_`` funnels can be used for the latter, while anythign else should be used former the former.


"""

import typing
import enum
import operator
import itertools
import collections
import builtins
import functools
import copy

from . import _helpers
from . import _colors


__all__ = (
    'text_replace', 'JustType', 'text_min_horizontal', 'text_min_vertical', 'text_max_horizontal', 'text_max_vertical',
    'text_max_dynamic', 'text_bloat_horizontal', 'text_bloat_vertical', 'text_block', 'text_paint', 'mesh_delegate',
    'mesh_delimit', 'mesh_focal', 'mesh_light', 'mesh_point', 'mesh_max', 'mesh_min', 'mesh_grid_fill', 'mesh_grid', 
    'mesh_head', 'mesh_flip', 'line_delimit'
)


def _call_direct(function):

    def direct(*args, **kwargs):
        *args, lines, point = args
        return function(*args, **kwargs)(lines, point)
    
    function.call = direct

    return function


def _text_replace(rune,
                  lines, point):

    get_rune = rune if callable(rune) else lambda *args: rune
    
    for line in lines:
        for index in range(len(line)):
            line[index] = get_rune(line[index])


@_call_direct
def text_replace(rune: typing.Union[str, typing.Callable[[str], str]]):

    """
    Replace every line element.

    :param rune:
        The rune to replace with, or a function that takes the current rune and returns the replacement.

    .. code-block::

        'The quic k brown fox'
        'jumps ov|er the lazy dog'
        'and fall s on its face'

        >>> text_replace('*')

        '******** ***********'
        '********|***************'
        '******** *************'
    """

    return functools.partial(_text_replace, rune)


class JustType(str, enum.Enum):

    """
    JustType()

    Denotes the type of alignment.
    """
    
    #: left or top
    start = 'start'
    #: right or bottom
    end = 'end'
    #: middle
    center = 'center'


def _text_min_horizontal(just, size, rune, 
                         lines, point):

    max_line_size = builtins.max(map(len, lines)) if size is None else size

    for rol_y, rol_line in enumerate(lines):
        padding_size = max_line_size - len(rol_line)
        if not padding_size > 0:
            continue
        if just == JustType.start:
            padding_size_left = 0
            padding_size_right = padding_size
        elif just == JustType.end:
            padding_size_left = padding_size
            padding_size_right = 0
        elif just == JustType.center:
            padding_size_left = padding_size // 2
            padding_size_right = padding_size - padding_size_left
        rol_line[0:0] = (rune,) * padding_size_left
        rol_line.extend((rune,) * padding_size_right)
        if rol_y == point[0]:
            point[1] += padding_size_left


@_call_direct
def text_min_horizontal(just: JustType, 
                        size: int, 
                        rune: str):
    
    """
    Ensure each line is at least of a certain length, aligned accordingly using a rune.
    
    :param just:
        Denotes justification to align with.
    :param size:
        The minimum length of each line.
    :param rune:
        The rune used to fill empty space.

    .. code-block::

        'The quic k brown fox'
        'jumps ov|er the lazy dog'
        'and fall s on its face'

        >>> text_min_horizontal(JustType.center, 25, ' ')

        '   The qu ick brown fox   '
        ' jumps ov|er the lazy dog '
        '  and fal ls on its face  '
    """

    return functools.partial(_text_min_horizontal, just, size, rune)


def _text_min_vertical(just, size, rune,
                       lines, point):

    lines_size = len(lines) if size is None else size

    padding_size = lines_size - len(lines)

    if not padding_size > 0:
        return

    if just == JustType.start:
        padding_size_top = 0
        padding_size_bottom = padding_size
    elif just == JustType.end:
        padding_size_top = padding_size
        padding_size_bottom = 0
    elif just == JustType.center:
        padding_size_top = padding_size // 2
        padding_size_bottom = padding_size - padding_size_top

    max_line_size = builtins.max(map(len, lines))

    lines[0:0] = ([rune] * max_line_size for _ in range(padding_size_top))
    lines.extend(([rune] * max_line_size for _ in range(padding_size_bottom)))

    point[0] += padding_size_top


@_call_direct
def text_min_vertical(just: JustType, 
                      size: int, 
                      rune: str):
    
    """
    Ensure there is at least a certain amount of lines, aligned accordingly using a rune.

    :param just:
        Denotes justification to align with.
    :param size:
        The minimum amount lines.
    :param rune:
        The rune used to create lines to fill empty space.

    .. code-block::

        'The quic k brown fox'
        'jumps ov|er the lazy dog'
        'and fall s on its face'

        >>> text_min_vertical(JustType.end, 5, '~')

        '~~~~~~~~ ~~~~~~~~~~~~~~~'
        '~~~~~~~~ ~~~~~~~~~~~~~~~'
        'The quic k brown fox    '
        'jumps ov|er the lazy dog'
        'and fall s on its face  '
    """

    return functools.partial(_text_min_vertical, just, size, rune)


def _text_max_horizontal(size,
                         lines, point):

    cur_y = point[0]
    cur_x = point[1]
    cur_line = lines[cur_y]

    min_max_x = size
    max_max_x = len(cur_line)
    min_min_x = 0
    max_min_x = max_max_x - min_max_x

    cut_x = size // 2

    min_x = builtins.max(min_min_x, builtins.min(max_min_x, cur_x - cut_x))
    max_x = builtins.max(min_max_x, builtins.min(max_max_x, min_x + size))

    for rol_line in lines:
        rol_line[max_x:] = rol_line[:min_x] = ()

    point[1] = cur_x - min_x


@_call_direct
def text_max_horizontal(size: int):
    
    """
    Ensure each line is at most a certain size, ensuring the cursor is visible.

    :param size:
        The maximum length of each line.

    .. code-block::

        'The quic k brown fox'
        'jumps ov|er the lazy dog'
        'and fall s on its face'

        >>> text_max_horizontal(10)

        ' quic k bro'
        'ps ov|er th'
        ' fall s on '
    """

    return functools.partial(_text_max_horizontal, size)


def _text_max_vertical(size,
                       lines, point):

    cur_y = point[0]

    min_max_y = size
    max_max_y = len(lines)
    min_min_y = 0
    max_min_y = max_max_y - min_max_y

    cut_y = size // 2

    min_y = builtins.max(min_min_y, builtins.min(max_min_y, cur_y - cut_y))
    max_y = builtins.max(min_max_y, builtins.min(max_max_y, min_y + size))

    lines[max_y:] = lines[:min_y] = ()

    point[0] = cur_y - min_y


@_call_direct
def text_max_vertical(size: int):
    
    """
    Ensure there is at most a certain amount of lines, ensuring the cursor is visible.

    :param size:
        The maximum amount of lines.

    .. code-block::

        'The quic k brown fox'
        'jumps ov|er the lazy dog'
        'and fall s on its face'

        >>> text_max_vertical(1)

        'jumps ov|er the lazy dog'
    """

    return functools.partial(_text_max_vertical, size)


def _text_max_dynamic(get,
                      lines, point):
    
    functions = (_text_max_vertical, _text_max_horizontal)
    
    sizes = get()

    for function, size in zip(functions, sizes):
        function(size, lines, point)


@_call_direct
def text_max_dynamic(get: typing.Callable[[], typing.Tuple[int, int]]):
    
    """
    A combination of :func:`.text_max_horizontal` and :func:`.text_max_vertical`.
    
    :param get:
        Should return an iterable with each function's size on their axis index.
    """

    return functools.partial(_text_max_dynamic, get)


def _text_bloat_horizontal(just, size, runes,
                           lines, point):

    push = builtins.max(map(len, lines))

    for index, rune in enumerate(runes):
        _text_min_horizontal(just, size + push + index, rune, lines, point)


@_call_direct
def text_bloat_horizontal(just: JustType, 
                          size: int, 
                          rune: str):
    
    """
    Increase each line's length to a certain size, aligned by an axis using a rune.

    :param just:
        Denotes justification to align with.
    :param size:
        The additional length of the longest line, applied as minimum to all.
    :param rune:
        The rune used to fill empty space.

    .. code-block::

        'The quic k brown fox'
        'jumps ov|er the lazy dog'
        'and fall s on its face'

        >>> text_bloat_horizontal(JustType.start, 2, '%')

        'The quic k brown fox%%%%%%'
        'jumps ov|er the lazy dog%%'
        'and fall s on its face%%%%'
    """

    return functools.partial(_text_bloat_horizontal, just, size, rune)


def _text_bloat_vertical(just, size, runes,
                         lines, point):

    push = len(lines)

    for index, rune in enumerate(runes):
        _text_min_vertical(just, size + push + index, rune, lines, point)


@_call_direct
def text_bloat_vertical(just: JustType, 
                        size: int, 
                        rune: str):
    
    """
    Increase the amount of lines lines to a certain size, aligned by an axis using a rune.

    :param just:
        Denotes justification to align with.
    :param size:
        The additional amount lines.
    :param rune:
        The rune used to create lines to fill empty space.

    .. code-block::

        'The quic k brown fox'
        'jumps ov|er the lazy dog'
        'and fall s on its face'

        >>> text_bloat_vertical(JustType.center, 2, '%')

        '%%%%%%%% %%%%%%%%%%%%%%%'
        'The quic k brown fox'
        'jumps ov|er the lazy dog'
        'and fall s on its face'
        '%%%%%%%% %%%%%%%%%%%%%%%'
    """

    return functools.partial(_text_bloat_vertical, just, size, rune)


def _text_block(rune_top, rune_bottom, rune_left, rune_right,
                rune_top_left, rune_top_right, rune_bottom_left, rune_bottom_right,
                lines, point):

    if rune_top:
        line = lines[0]
        size = len(line)
        line[:] = (rune_top,) * size

    if rune_bottom:
        line = lines[- 1]
        size = len(line)
        line[:] = (rune_top,) * size

    if rune_left:
        for line in lines:
            line[0] = rune_left
    
    if rune_right:
        for line in lines:
            line[- 1] = rune_right

    if rune_top_left:
        lines[0][0] = rune_top_left

    if rune_top_right:
        lines[0][- 1] = rune_top_right

    if rune_bottom_left:
        lines[- 1][0] = rune_bottom_left

    if rune_bottom_right:
        lines[- 1][ -1] = rune_bottom_right


@_call_direct
def text_block(rune_top: str, 
               rune_bottom: str, 
               rune_left: str, 
               rune_right: str,
               rune_top_left: str, 
               rune_top_right: str, 
               rune_bottom_left: str, 
               rune_bottom_right: str):
    
    """
    Surround the lines by overwriting with the respective runes. Any of them can be :code:`None` to ignore.

    :param rune_top:
        Used on the first line.
    :param rune_bottom: 
        Used on the last line.
    :param rune_left:
        Used on the first rune of each line.
    :param rune_right:
        Used on the last rune of each line.
    :param rune_top_left:
        Used on the first rune of the first line.
    :param rune_top_right:
        Used on the last rune of the first line.
    :param rune_bottom_left:
        Used on the first rune of the last line.
    :param rune_bottom_right:
        Used on the last rune of the last line.

    .. code-block::

        'The quic k brown fox'
        'jumps ov|er the lazy dog'
        'and fall s on its face'

        >>> text_block('-', '-', '|', '|', '/', '\\', '\\', '/')

        '/----------------------\\'
        '|umps ov|er the lazy do|'
        '\\----------------------/'

    Use :code:`text_bloat_vertical(JustType.center, 2, ' ')` and :code:`text_bloat_horizontal(JustType.center, 2, ' ')` before this to avoid content overwrite.
    """

    return functools.partial(
        _text_bloat_vertical, rune_top, rune_bottom, rune_left, rune_right,
        rune_top_left, rune_top_right, rune_bottom_left, rune_bottom_right
    )

  
def _text_paint(color, lines, point):

    if callable(color):
        color = color()

    if color is None:
        return

    _helpers.paint_lines(color, lines)


@_call_direct
def text_paint(color: str):

    """
    Paint each rune of each line.

    :param color:
        The color to paint with.

    .. code-block::

        'The quic k brown fox'
        'jumps ov|er the lazy dog'
        'and fall s on its face'

        >>> text_paint('\x1b[36m')

        # The same, but in light blue.
    """

    return functools.partial(_text_paint, color)


def _mesh_delegate(check, aware, function, 
                   tiles, point):

    for spot, tile in tiles.items():
        if check and not check(spot, tile):
            continue
        args = [*tile]
        if aware:
            args.insert(0, spot)
        function(*args)


@_call_direct
def mesh_delegate(function: typing.Callable[[typing.List[typing.List[str]], typing.List[int]], None], 
                  check   : typing.Callable[[typing.Tuple[int, int], typing.List[typing.List[typing.List[str]]], typing.List[int]], bool] = None, 
                  aware   : bool = False):
    
    """
    Call a function on each tile of the mesh.

    :param function:
        The function called.
    :param check:
        Used as :code:`(spot, tile) -> bool` to denote whether the specific tile gets ignored.
    :param aware:
        Whether to prepend the tile's ``spot`` to the function's arguments.
    """

    return functools.partial(_mesh_delegate, check, aware, function)


def _mesh_delimit(axis, rune,
                  tiles, point):
    
    all_a = (spot[axis] for spot in tiles)
    max_a = max(all_a)

    def check(spot, tile):
        return spot[axis] < max_a
    
    bloat = _text_bloat_horizontal if axis else _text_bloat_vertical

    function = functools.partial(bloat, JustType.start, 1, rune)

    _mesh_delegate(check, False, function, tiles, point)


@_call_direct
def mesh_delimit(axis: int, 
                 text: str):
    
    """
    Insert text between tiles.

    :param axis:
        The axis considered for the operation.
    :param text:
        The text to insert.
    """

    return functools.partial(_mesh_delimit, axis, text)


def _mesh_focal(function,
                tiles, point):
    
    main_spot = tuple(point)

    def delegate_function(spot, *tile):
        current = spot == main_spot
        function(current, *tile)

    _mesh_delegate(None, True, delegate_function, tiles, point)


@_call_direct
def mesh_focal(function):
    
    """
    Call a function on each tile of the mesh, with a :class:`bool` denoting whether it's the pointed tile prepended in the arguments.

    :param function:
        The function called.
    """

    return functools.partial(_mesh_focal, function)


def _mesh_light(focus_color, evade_color, 
                tiles, point):
    
    colors = (evade_color, focus_color)
    
    def function(current, *tile):
        color = colors[current]
        _text_paint(color, *tile)
    
    _mesh_focal(function, tiles, point)


@_call_direct
def mesh_light(focus_color: typing.Union[str, None] = None,
               evade_color: typing.Union[str, None] = None):
    
    """
    Paint the mesh's tiles depending on whether they are pointed.

    :param focus_color:
        The color used for the pointed tile.
    :param evade_color:
        The color used for the other tiles.
    """

    return functools.partial(_mesh_light, focus_color, evade_color)


def _mesh_point(focus_rune, evade_rune, tiles, point):

    runes = (evade_rune, focus_rune)

    def function(current, lines, point):
        rune = runes[current]
        size = len(rune)
        fill = size * ' '
        for index, line in enumerate(lines):
            text = fill if index else rune
            line[0:0] = text
        point[1] += size
    
    _mesh_focal(function, tiles, point)


@_call_direct
def mesh_point(focus_rune: str,
               evade_rune: str):
    
    """
    Prepend a rune to the pointed tile's first line and another to all others.

    All other lines have empty characters prepended to align with the first.

    :param focus_rune:
        The rune for the pointed tile.
    :param evade_rune:
        The rune for the other tiles.
    """

    return functools.partial(_mesh_point, focus_rune, evade_rune)


def _mesh_max(axis, size, 
              tiles, point):

    size -= 1

    cur_a = point[axis]

    all_a = set(map(operator.itemgetter(axis), tiles))
    min_a = builtins.min(all_a)
    max_a = builtins.max(all_a)

    cut_a = size // 2

    min_a = builtins.min(max_a - size, builtins.max(min_a, cur_a - cut_a))
    max_a = builtins.min(max_a, min_a + size)

    for spot in tuple(tiles):
        cur_a = spot[axis]
        if cur_a >= min_a and cur_a <= max_a:
            continue  
        del tiles[spot]


@_call_direct
def mesh_max(axis: int, 
             size: int):
    
    """
    Ensure there is most of a certain amount of tiles along an certain axis.

    :param axis:
        The axis considered for the operation.
    :param size:
        The maximum amount of tiles.
    """
    
    return functools.partial(_mesh_max, axis, size)


def _mesh_min(axis, just, size, fill,
              tiles, point):

    axis_oth = (axis - 1) % len(point) 

    all_a = set(map(operator.itemgetter(axis), tiles))
    min_a = builtins.min(all_a)
    max_a = builtins.max(all_a) 

    padding_size = size - (max_a - min_a)

    if not padding_size > 0:
        return

    if just == JustType.start:
        padding_size_start = 0
        padding_size_end = padding_size
    elif just == JustType.end:
        padding_size_start = padding_size
        padding_size_end = 0
    elif just == JustType.center:
        padding_size_start = padding_size // 2
        padding_size_end = padding_size - padding_size_start

    new_min_a = min_a - padding_size_start
    new_max_a = max_a + padding_size_end

    all_o = set(map(operator.itemgetter(axis_oth), tiles))
    min_o = builtins.min(all_o)
    max_o = builtins.max(all_o)

    new_range_a_start = range(new_min_a, min_a)
    new_range_a_end = range(max_a + 1, new_max_a + 1)

    for new_a in itertools.chain(new_range_a_start, new_range_a_end):
        for cur_o in range(min_o, max_o + 1):
            spot = [cur_o, cur_o]
            spot[axis] = new_a
            spot = tuple(spot)
            if spot in tiles:
                continue
            lines = fill(spot)
            tiles[spot] = (lines, [0, 0])


@_call_direct
def mesh_min(axis: int, 
             size: int, 
             just: JustType = JustType.start, 
             fill: typing.Callable[[typing.Tuple[int, int]], typing.List[typing.List[str]]] = lambda spot: [[]]):
    
    """
    Ensure there is most of a certain amount of tiles along an certain axis, aligned accordingly by ``fill``\\ing with new tiles.

    :param axis:
        The axis considered for the operation.
    :param size:
        The minimum amount of tiles.
    :param just:
        Denotes justification to align with.
    :param fill:
        Used as :code:`(spot) -> lines` to fill empty space.
    """
    
    return functools.partial(_mesh_min, axis, just, size, fill)


def _mesh_grid_fill(tile_just_vertical, tile_rune_vertical,
                    tile_just_horizontal, tile_rune_horizontal,
                    tile_min_vertical, tile_min_horizontal,
                    push_top, push_bottom, push_left, push_right,
                    tiles, point):
    
    col_x_group = collections.defaultdict(list)
    col_y_group = collections.defaultdict(list)

    sizes_vertical = collections.defaultdict(int)
    sizes_horizontal = collections.defaultdict(int)

    for cur_point, cur_tile in tiles.items():
        cur_y, cur_x = cur_point
        cur_tile_lines, cur_tile_point = cur_tile
        col_x_group[cur_y].append(cur_x)
        col_y_group[cur_x].append(cur_y)
        size_vertical = len(cur_tile_lines)
        sizes_vertical[cur_y] = builtins.max(sizes_vertical[cur_y], size_vertical, tile_min_vertical)
        size_horizontal = builtins.max(map(len, cur_tile_lines))
        sizes_horizontal[cur_x] = builtins.max(sizes_horizontal[cur_x], size_horizontal, tile_min_horizontal)

    bounds_x = {cur_y: (builtins.min(col_x), builtins.max(col_x)) for cur_y, col_x in col_x_group.items()}
    bounds_y = {cur_x: (builtins.min(col_y), builtins.max(col_y)) for cur_x, col_y in col_y_group.items()}

    spots = set()
    for cur_y, cur_bounds in bounds_x.items():
        min_x, max_x = cur_bounds
        for may_x in range(min_x, max_x + 1):
            spot = (cur_y, may_x)
            spots.add(spot)
    for cur_x, cur_bounds in bounds_y.items():
        min_y, max_y = cur_bounds
        for may_y in range(max_y, min_y, - 1):
            spot = (may_y, cur_x)
            spots.add(spot)

    min_y = builtins.min(bounds_x)
    max_y = builtins.max(bounds_x)
    all_y = range(max_y + push_top, min_y - 1 - push_bottom, - 1)

    min_x = builtins.min(bounds_y)
    max_x = builtins.max(bounds_y)
    all_x = range(min_x - push_left, max_x + 1 + push_right, 1)

    for spot in itertools.product(all_y, all_x):
        try:
            tile = tiles[spot]
        except KeyError:
            tile = tiles[spot] = ([[]], [0, 0])
        size_horizontal = sizes_horizontal[spot[1]]
        _text_min_horizontal(tile_just_horizontal, size_horizontal, tile_rune_horizontal, *tile)
        size_vertical = sizes_vertical[spot[0]]
        _text_min_vertical(tile_just_vertical, size_vertical, tile_rune_vertical, *tile)


@_call_direct
def mesh_grid_fill(tile_just_vertical  : JustType = JustType.start, 
                   tile_rune_vertical  : str      = ' ',
                   tile_just_horizontal: JustType = JustType.start, 
                   tile_rune_horizontal: str      = ' ',
                   tile_min_vertical   : int      = 0, 
                   tile_min_horizontal : int      = 0,
                   push_top            : int      = 0, 
                   push_bottom         : int      = 0, 
                   push_left           : int      = 0, 
                   push_right          : int      = 0):

    """
    Fill missing spots within a square so that all rows and columns align.

    For that to happen, tiles may need to grow to adjust for the size of others in each axis.

    :param tile_just_vertical:
        Denotes vertical justfication for growing each tile.
    :param tile_rune_vertical:
        The rune used when vertical growing each tile.
    :param tile_just_horizontal:
        Denotes horizontal justfication for growing each tile.
    :param tile_rune_horizontal:
        The rune used when horizontal growing each tile.
    :param tile_min_vertical:
        The minimum vertical size of each tile.
    :param tile_min_horizontal:
        The minimum horizontal size of each tile.
    :param push_top:
        The additional amount of horizontal groups of tiles injected over the final square.
    :param push_bottom:
        The additional amount of horizontal groups of tiles injected under the final square.
    :param push_left:
        The additional amount of vertical groups of tiles injected left of the final square.
    :param push_right:
        The additional amount of vertical groups of tiles injected right of the final square.
    """
    
    return functools.partial(
        _mesh_grid_fill, 
        tile_just_vertical, tile_rune_vertical,
        tile_just_horizontal, tile_rune_horizontal,
        tile_min_vertical, tile_min_horizontal,
        push_top, push_bottom, push_left, push_right
    )


def _mesh_grid_get_text_block_runes(get, spots, spot):

    cur_y, cur_x = spot

    got_current      = (cur_y    , cur_x    ) in spots
    got_top          = (cur_y + 1, cur_x    ) in spots
    got_left         = (cur_y    , cur_x - 1) in spots
    got_top_left     = (cur_y + 1, cur_x - 1) in spots

    # rune_top
    if got_current or got_top:
        yield get('horizontal')
    else:
        yield ' '

    yield None

    # rune_left
    if got_current or got_left:
        yield get('vertical')
    else:
        yield ' '
    
    yield None

    # rune_top_left
    if got_top and got_left:
        yield get('cross')
    elif got_current:
        if got_top_left:
            yield get('cross')
        elif got_top:
            yield get('cross_left')
        elif got_left:
            yield get('cross_top')
        else:
            yield get('top_left')
    elif got_top_left:
        if got_top:
            yield get('cross_bottom')
        elif got_left:
            yield get('cross_right')
        else:
            yield get('bottom_right')
    elif got_top:
        yield get('bottom_left')
    elif got_left:
        yield get('top_right')
    else:
        yield ' '


def _mesh_grid(runes, runes_color, tiles, point, **mesh_grid_fill_kwargs):

    @functools.lru_cache()
    def get_rune(name):
        rune = runes[name]
        if not runes_color is None:
            rune =_helpers.paint_rune(runes_color, rune)
        return rune

    spots = set(tiles)
    
    mesh_grid_fill.call(
        tiles, point, 
        **mesh_grid_fill_kwargs, 
        push_top = 0, push_bottom = 1, push_left = 0, push_right = 1
    )

    all_y = set(map(operator.itemgetter(0), tiles))
    min_y = builtins.min(all_y)

    all_x = set(map(operator.itemgetter(1), tiles))
    max_x = builtins.max(all_x)
    
    for spot, tile in tiles.items():
        text_block_runes = tuple(_mesh_grid_get_text_block_runes(get_rune, spots, spot))
        if spot[0] > min_y:
            _text_bloat_vertical(JustType.end, 1, ' ', *tile)
        _text_bloat_horizontal(JustType.end, 1, ' ', *tile)
        _text_block(*text_block_runes, None, None, None, *tile)

    for spot, tile in tuple(tiles.items()):
        cur_y, cur_x = spot
        if cur_y == min_y and cur_x == max_x:
            old_spot = (cur_y + 1, cur_x - 1)
            old_tile = tiles[old_spot]
            new_rune = tile[0][0][0]
            old_tile[0][- 1].append(new_rune)
        elif cur_y == min_y:
            old_spot = (cur_y + 1, cur_x)
            old_tile = tiles[old_spot]
            new_line = tile[0][0]
            old_tile[0].append(new_line)
        elif cur_x == max_x:
            old_spot = (cur_y, cur_x - 1)
            old_tile = tiles[old_spot]
            for old_line, new_line in zip(old_tile[0], tile[0]):
                old_line.append(new_line[0])
        else:
            continue
        del tiles[spot]
        

@_call_direct
def mesh_grid(runes: typing.Dict[str, str] = {
                'horizontal': '─',
                'vertical': '│',
                'cross': '┼',
                'cross_top': '┬',
                'cross_bottom': '┴',
                'cross_left': '├',
                'cross_right': '┤',
                'top_left': '┌',
                'top_right': '┐',
                'bottom_left': '└',
                'bottom_right': '┘'
              }, 
              runes_color: str = _colors.basic('black.lite'),
              **fill_kwargs):
    
    """
    Turns a mesh into a grid using.
     
    :param runes:
        The collection of runes used for drawing around each tile.
    :param runes_color:
        Used to paint all provided grid runes.

    Additional arguments get passed to :func:`.mesh_grid_fill` before the operation.
    """

    return functools.partial(_mesh_grid, runes, runes_color, **fill_kwargs)


def _mesh_head(axis, just, skip, min, get,
               tiles, point):

    dimensions = len(point)

    axis_oth = (axis - 1) % dimensions

    all_a = set(map(operator.itemgetter(axis), tiles))
    min_a = builtins.min(all_a)
    max_a = builtins.max(all_a)

    all_o = map(operator.itemgetter(axis_oth), tiles)

    size = builtins.max(min, max_a - min_a + 1)

    if axis:
        max_a = min_a + size
        range_a = range(min_a, max_a, + 1)
        if just is None:
            just = JustType.start
    else:
        min_a = max_a - size
        range_a = range(max_a, min_a, - 1)
        if just is None:
            just = JustType.end

    if just is JustType.start:
        max_o = builtins.max(all_o)
        cur_o = max_o + 1
    elif just is JustType.end:
        min_o = builtins.min(all_o)
        cur_o = min_o - 1
    else:
        raise ValueError(f'invalid just: {just}')

    for cur_i, cur_a in enumerate(range_a):
        if cur_i < skip:
            continue
        lines = get(cur_a)
        if lines is None:
            continue
        point = [0, 0]
        tile = (lines, point)
        spot = [cur_o] * dimensions
        spot[axis] = cur_a
        spot = tuple(spot)
        tiles[spot] = tile


@_call_direct
def mesh_head(axis: int, 
              get : typing.Callable[[int], typing.List[typing.List[str]]], 
              just: typing.Union[JustType, None] = None,
              skip: int = 0, 
              min : int = 0):
    
    """
    Add headers to the mesh.
    
    :param axis:
        The axis along which to add headers.
    :param get:
        Used as :code:`(index) -> lines` on each row or column for fetching its header.
    :param just:
        Denotes justification to align with. Default is left/top.
    :param skip:
        The amount of rows or columns to ignore at the beginning of the operation.
    :param min:
        The minimum amount of headers to be added. Can be used to avoid possible gaps.

    .. code-block::

        mesh_head(0, lambda index: [list(str(index))], min = 10)
        # skip is used to prevent adding a header for the headers row.
        mesh_head(1, lambda index: [list(str(index))], min = 10, skip = 1)
    """
    
    return functools.partial(_mesh_head, axis, just, skip, min, get)


def _mesh_flip(axis,
               tiles, point):
    
    flip = lambda iterable: tuple(value * - 1 for value in iterable)
    
    temp = {}
    for spot in tuple(tiles):
        tile = tiles.pop(spot)
        spot = flip(spot)
        temp[spot] = tile
    
    tiles.update(temp)

    point[:] = flip(point)


@_call_direct
def mesh_flip(axis: int):
    
    """
    Flip a mesh's axis.
    
    :param axis:
        The axis to flip.
    """
    
    return functools.partial(_mesh_flip, axis)


def _line_delimit(text,
                  tiles, point):
    
    main_lines = _helpers.split_lines(text)

    for index in range(1, len(tiles) * 2 - 1, 2):
        main_lines_copy = copy.deepcopy(main_lines)
        tiles.insert(index, (main_lines_copy, [0, 0]))
        if point[0] > index:
            continue
        point[0] += 1


@_call_direct
def line_delimit(text: str):

    """
    Insert text between tiles.

    :param text:
        The text to insert.
    """
    
    return functools.partial(_line_delimit, text)