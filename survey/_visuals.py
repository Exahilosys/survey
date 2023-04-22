
"""
Classes for transforming specific-structure data into a form that be 
used by to print to the console while maintaining proper cursor position.

Most accept data structured in similar ways to how it is used in :class`~.mutate.Mutate`\ s.
"""

import typing
import abc
import copy
import math

from . import _core


__all__ = ('Visual', 'Text', 'Mesh', 'Line')


_type_Visual_init_get         : typing.TypeAlias = typing.Callable[[bool, bool], tuple[typing.Any]]
_type_Visual_init_funnel_enter: typing.TypeAlias = typing.Callable[[typing.Unpack[typing.Any]], None] | None
_type_Visual_init_funnel_leave: typing.TypeAlias = typing.Callable[[_core._type_Render_draw_lines, _core._type_Render_draw_point], None] | None

_type_Visual_get_enter        : typing.TypeAlias = bool
_type_Visual_get_leave        : typing.TypeAlias = bool
_type_Visual_get_return       : typing.TypeAlias = tuple[_core._type_Render_draw_lines, _core._type_Render_draw_point] | None


class Visual(abc.ABC):

    """
    Base class for transformers of data into lines and point for rendering.

    :param get:
        Used for fetching the data.
        The arguments have the same meaning as in :meth:`.get`.
    :param funnel_enter:
        Used for mutating the data in-place before turning into lines and point.
    :param funnel_leave:
        Used for mutating the resulting lines and point in-place after transforming the data.
    """

    __slots__ = ('_get', '_funnel_enter', '_funnel_leave')

    def __init__(self, 
                 get         : _type_Visual_init_get, 
                 funnel_enter: _type_Visual_init_funnel_enter = None,
                 funnel_leave: _type_Visual_init_funnel_leave = None):

        self._get = get

        self._funnel_enter = funnel_enter
        self._funnel_leave = funnel_leave

    @abc.abstractmethod
    def _format(self, *args):

        return NotImplemented

    def get(self, 
            enter: _type_Visual_get_enter = True, 
            leave: _type_Visual_get_leave = True) -> _type_Visual_get_return:

        """
        Fetches and transforms the data.

        :param enter:
            Whether to use ``funnel_enter``.
        :param leave:
            Whether to use ``funnel_leave``.
        
        :return:
            The final lines and point.
        """

        assets = self._get(enter, leave)

        assets = copy.deepcopy(assets)

        if enter and not self._funnel_enter is None:
            self._funnel_enter(*assets)

        (lines, point) = self._format(*assets)

        if leave and not self._funnel_leave is None:
            self._funnel_leave(lines, point)

        return (lines, point)


_type_Text_link_lines       : typing.TypeAlias = list[list[str]]
_type_Text_link_point       : typing.TypeAlias = list[int, int]

_type_Text_init_get         : typing.TypeAlias = typing.Callable[[bool, bool], tuple[_type_Text_link_lines, _type_Text_link_point]]
_type_Text_init_funnel_enter: typing.TypeAlias = typing.Callable[[_type_Text_link_lines, _type_Text_link_point], None] | None
_type_Text_init_funnel_leave: typing.TypeAlias = _type_Visual_init_funnel_leave


class Text(Visual):

    """
    Transforms lines and point into... lines and cursor point.

    :param get:
        Used for fetching ``data``.
    :param funnel_enter:
        Used for mutating ``data`` in-place before turning into ``(lines, point)``.
    :param funnel_leave:
        Used for mutating the resulting ``(lines, point)`` in-place after transforming ``data``.
    """

    __slots__ = ()

    def __init__(self, 
                 get         : _type_Text_init_get, 
                 funnel_enter: _type_Text_init_funnel_enter = None,
                 funnel_leave: _type_Text_init_funnel_leave = None):
        
        super().__init__(get, funnel_enter, funnel_leave)

    @classmethod
    def link(cls, 
             lines: _type_Text_link_lines, 
             point: _type_Text_link_point, 
             *args, **kwargs):

        """
        Use this if ``(lines, point)`` are expected to be mutated in-place over their life time.
        """

        def get(*args):
            return (lines, point)

        return cls(get, *args, **kwargs)

    def _format(self, lines, point):

        return (lines, point)
    

_type_Mesh_link_tiles       : typing.TypeAlias = dict[tuple[int, int], tuple[_type_Text_link_lines, _type_Text_link_point]]
_type_Mesh_link_point       : typing.TypeAlias = list[int, int]

_type_Mesh_init_get         : typing.TypeAlias = typing.Callable[[bool, bool], tuple[_type_Mesh_link_tiles, _type_Mesh_link_point]]
_type_Mesh_init_funnel_enter: typing.TypeAlias = typing.Callable[[_type_Mesh_link_tiles, _type_Mesh_link_point], None] | None
_type_Mesh_init_funnel_leave: typing.TypeAlias = _type_Visual_init_funnel_leave


class Mesh(Visual):

    """
    Transforms mesh tiles and point into lines and cursor point.

    :param get:
        Used for fetching ``(tiles, point)``.
    :param funnel_enter:
        Used for mutating ``(tiles, point)`` in-place before turning into ``(lines, point)``.
    :param funnel_leave:
        Used for mutating the resulting ``(lines, point)`` in-place after transforming ``(tiles, point)``.

    - ``tiles`` is ``{spot: tile, ...}``
    - ``spot`` is ``(y, x)``
    - ``tile`` is ``(lines, point)``
    """

    __slots__ = ()

    def __init__(self, 
                 get         : _type_Mesh_init_get, 
                 funnel_enter: _type_Mesh_init_funnel_enter = None,
                 funnel_leave: _type_Mesh_init_funnel_leave = None):
        
        super().__init__(get, funnel_enter, funnel_leave)

    @classmethod
    def link(cls, 
             tiles: _type_Mesh_link_tiles, 
             point: _type_Mesh_link_point, 
             *args, **kwargs):

        """
        Use this if ``(tiles, point)`` are expected to be mutated in-place over their life time.

        - ``tiles`` is ``{spot: get, ...}``
        - ``spot`` is ``(y, x)``
        - ``get`` is like :meth:`.get` and returns ``(lines, point)``
        """

        def get(*args):
            dyn_tiles = {spot: get(*args) for (spot, get) in tiles.items()}
            dyn_point = copy.deepcopy(point)
            return (dyn_tiles, dyn_point)
        
        return cls(get, *args, **kwargs)

    def _format(self, tiles, point):

        spots = tiles.keys()

        (main_y, main_x) = point

        done_lines = []
        memo_lines = []
        memo_y = - math.inf

        fin_y = 0
        fin_x = 0

        for spot in sorted(spots):
            (spot_y, spot_x) = spot
            (tile_lines, tile_point) = tiles[spot]
            (tile_point_y, tile_point_x) = tile_point
            if not spot_y == memo_y:
                if spot_y <= main_y:
                    fin_y += len(memo_lines)
                done_lines[0:0] = memo_lines
                memo_y = spot_y
                memo_lines.clear()
            if spot_y == main_y and spot_x == main_x:
                fin_y += len(tile_lines) - tile_point_y
                try:
                    memo_line = memo_lines[tile_point_y]
                except IndexError:
                    ext_x = 0
                else:
                    ext_x = len(memo_line)
                fin_x = ext_x + tile_point_x
            for (tile_line_index, tile_line) in enumerate(tile_lines):
                try:
                    memo_line = memo_lines[tile_line_index]
                except IndexError:
                    memo_line = []
                    memo_lines.append(memo_line)
                memo_line.extend(tile_line)

        done_lines[0:0] = memo_lines

        fin_y = len(done_lines) - fin_y

        done_point = [fin_y, fin_x]

        return (done_lines, done_point)


_type_Line_link_tiles       : typing.TypeAlias = dict[tuple[int, int], tuple[_type_Text_link_lines, _type_Mesh_link_point]]
_type_Line_link_point       : typing.TypeAlias = list[int]

_type_Line_init_get         : typing.TypeAlias = typing.Callable[[bool, bool], tuple[_type_Line_link_tiles, _type_Line_link_point]]
_type_Line_init_funnel_enter: typing.TypeAlias = typing.Callable[[_type_Line_link_tiles, _type_Line_link_point], None] | None
_type_Line_init_funnel_leave: typing.TypeAlias = _type_Visual_init_funnel_leave


class Line(Visual):

    """
    Transforms a list of tiles and point into lines and cursor point.

    :param get:
        Used for fetching ``(tiles, point)``.
    :param funnel_enter:
        Used for mutating ``(tiles, point)`` in-place before turning into ``(lines, point)``.
    :param funnel_leave:
        Used for mutating the resulting ``(lines, point)`` in-place after transforming ``(tiles, point)``.

    - ``tiles`` is ``[get, ...]``
    - ``get`` is like :meth:`.get` and return ``(lines, point)``
    """

    __slots__ = ()

    def __init__(self, 
                 get         : _type_Line_init_get, 
                 funnel_enter: _type_Line_init_funnel_enter = None,
                 funnel_leave: _type_Line_init_funnel_leave = None):
        
        super().__init__(get, funnel_enter, funnel_leave)

    @classmethod
    def link(cls, 
             tiles: _type_Line_link_tiles, 
             point: _type_Line_link_point, 
             *args, **kwargs):

        """
        Use this if ``(tiles, point)`` are expected to be mutated in-place over their life time.

        - ``tiles`` is ``[get, ...]``
        - ``get`` is like :meth:`.get`
        """

        def get(*args):
            dyn_tiles = [get(*args) for get in tiles]
            dyn_point = copy.deepcopy(point)
            return (dyn_tiles, dyn_point)
        
        return cls(get, *args, **kwargs)

    def _format(self, tiles, tiles_point):

        tiles_index = tiles_point[0]

        fin_y = 0
        fin_x = 0

        lines = [[]]
        for (tile_index, (tile_lines, tile_point)) in enumerate(tiles):
            if tile_index < tiles_index:
                fin_y += len(tile_lines) - 1
            elif tile_index == tiles_index:
                fin_y += tile_point[0]
                fin_x = tile_point[1]
                if not fin_y:
                    fin_x += len(lines[fin_y])
            try:
                line = tile_lines.pop(0)
            except IndexError:
                continue
            lines[- 1].extend(line)
            lines.extend(tile_lines)

        point = [fin_y, fin_x]

        return (lines, point)

