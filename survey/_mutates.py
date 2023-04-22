
"""
Classes for changing data in-place in ways that emulate commonly-used interfaces.
"""

import typing
import abc
import types
import copy

from . import _helpers


__all__ = ('Error', 'Mutate', 'Cursor', 'Text', 'Mesh')


class Error(_helpers.InfoErrorMixin, Exception):

    __slots__ = ()


class Mutate(abc.ABC):

    """
    Base class for mutates. They emulate the behavior of common data manipulators.
    """

    __slots__ = ()

    class _State(types.SimpleNamespace):

        __slots__ = ()

    @abc.abstractmethod
    def _get_state(self):

        return NotImplemented
    
    def get_state(self):

        """
        Get a copy of the current state.
        """

        return self._get_state()
    
    @abc.abstractmethod
    def _set_state(self, state):

        return NotImplemented
    
    def set_state(self, state):

        """
        Restore the current state to the one provided.
        """

        return self._set_state(state)
    

_type_cursor_point: typing.TypeAlias = list[int]
    

class Cursor(Mutate):

    """
    A mutate for a point representing a position in space.

    :param point:
        The manipulating point.
    """

    __slots__ = ('_point',)

    def __init__(self, 
                 point: _type_cursor_point):

        self._point = point

    @property
    def point(self) -> _type_cursor_point:

        """
        The internal point.
        """

        return self._point
    
    def _get_state(self):
        
        point = copy.copy(self._point)

        return self._State(point = point)
    
    def _set_state(self, state):

        self._point[:] = state.point
    
    def _move(self, instructions):

        for (axis, coordinate) in instructions:
            self._point[axis] = coordinate

    def move(self, 
             instructions: list[tuple[int, int]]) -> None:

        """
        Move according to the instructions given. 
        
        Each instruction should be of ``(index, new_coordinate)`` form.
        """

        self._move(instructions)


_type_Text_init_rune : typing.TypeAlias = str
_type_Text_init_line : typing.TypeAlias = list[_type_Text_init_rune]
_type_Text_init_lines: typing.TypeAlias = list[_type_Text_init_line]
_type_Text_init_point: typing.TypeAlias = _type_cursor_point


class Text(Mutate):

    """
    A mutate for a block of text and a cursor among it.

    :param lines:
        The manipulating list of lines.
    :param point:
        The point for the cursor.
    """

    __slots__ = ('_lines', '_cursor')

    def __init__(self, 
                 lines: _type_Text_init_lines, 
                 point: _type_Text_init_point):

        self._lines = lines
        self._cursor = Cursor(point)

    @property
    def lines(self) -> _type_Text_init_lines:

        """
        The current lines.
        """

        return self._lines

    @property
    def _point(self):

        return self._cursor.point

    @property
    def point(self) -> _type_Text_init_point:

        """
        The current cursor's point.
        """

        return self._point
    
    def _get_state(self):

        lines = copy.deepcopy(self._lines)

        cursor = self._cursor.get_state()

        return self._State(
            lines = lines,
            cursor = cursor
        )
    
    def _set_state(self, state):

        self._lines[:] = state.lines

        self._cursor.set_state(state.cursor)

    def _insert(self, runes):

        cur_y = self._point[0]
        
        cur_x = self._point[1]

        cur_lines = self._lines
        
        cur_line = cur_lines[cur_y]

        cur_line[cur_x:cur_x] = runes

    def insert(self, 
               runes: list[str]):

        """
        Insert text at the current cursor position and move it accordingly.

        :param runes:
            The runes to insert.
        """

        self._insert(runes)

    def _move_y(self, size):

        cur_y = self._point[0]
        cur_x = self._point[1]
        cur_lines = self._lines
        
        new_y = cur_y + size

        max_y = len(cur_lines) - 1
        
        if not 0 <= new_y <= max_y:
            raise Error('insufficient_y_space', size = size)

        new_line = cur_lines[new_y]

        instructions = [(0, new_y)]

        may_x = len(new_line)

        if cur_x > may_x:
            instructions.append((1, may_x))

        self._cursor.move(instructions)

    def move_y(self, 
               size: int):
        
        """
        Move the cursor verticaly, wrapping to the max width of the new line as necessary.

        :param size:
            The amount of lines to move by.
        """

        self._move_y(size)

    def _move_x(self, size):

        cur_y = self._point[0]
        cur_x = self._point[1]
        cur_lines = self._lines

        cur_i = _helpers.text_point_to_index(cur_lines, cur_y, cur_x)

        min_i = 0
        max_i = sum(map(len, cur_lines)) + len(cur_lines) - 1

        new_i = cur_i + size

        if not min_i <= new_i <= max_i:
            raise Error('insufficient_x_space', size = size)

        (new_y, new_x) = _helpers.text_index_to_point(cur_lines, new_i)

        instructions = ((0, new_y), (1, new_x))

        self._cursor.move(instructions)

    def move_x(self, 
               size: int):

        """
        Move the cursor horizontally, wrapping to the next or last line as necessary.

        :param size:
            The amount of runes to move by.
        """

        self._move_x(size)

    def _delete(self, size):

        cur_y = self._point[0]
        cur_x = self._point[1]
        
        cur_lines = self._lines
        cur_line = cur_lines[cur_y]

        cur_i = _helpers.text_point_to_index(cur_lines, cur_y, cur_x)

        max_i = sum(map(len, cur_lines)) + len(cur_lines) - 1

        new_i = cur_i + size

        if not new_i <= max_i:
            raise Error('insufficient_x_space', size = size)

        (new_y, new_x) = _helpers.text_index_to_point(cur_lines, new_i)

        if not cur_y == new_y:
            psh_y = cur_y + 1
            cur_lines[psh_y:new_y] = ()
            mrg_line = cur_lines.pop(psh_y)
            new_x += len(cur_line)
            cur_line.extend(mrg_line)

        cur_line[cur_x:new_x] = ()

    def delete(self, 
               size: int):

        """
        Delete ahead of the cursor, including newlines.

        :param size:
            The amount of runes to delete.
        """

        self._delete(size)

    def _newline(self):

        cur_y = self._point[0]
        cur_x = self._point[1]
        
        cur_lines = self._lines
        cur_line = cur_lines[cur_y]

        new_line = cur_line[cur_x:]

        cur_line[cur_x:] = ()

        psh_y = cur_y + 1

        cur_lines.insert(psh_y, new_line)

        instructions = ((0, psh_y), (1, 0))

        self._cursor.move(instructions)

    def newline(self):

        """
        Insert a new line under the cursor, cutting the current one as necessary.
        """

        self._newline()


_type_Mesh_init_clean : typing.TypeAlias = None | int
_type_Mesh_init_spot  : typing.TypeAlias =        tuple[int, int]
_type_Mesh_init_tile  : typing.TypeAlias =        typing.Any
_type_Mesh_init_tiles : typing.TypeAlias =        dict[_type_Mesh_init_spot, _type_Mesh_init_tile]
_type_Mesh_init_point : typing.TypeAlias =        _type_cursor_point
_type_Mesh_init_score : typing.TypeAlias = None | typing.Callable[[_type_Text_init_lines, _type_Mesh_init_tile], int | None]
_type_Mesh_init_scout : typing.TypeAlias = None | typing.Callable[[_type_Mesh_init_spot], bool]
_type_Mesh_init_rigid : typing.TypeAlias =        bool
_type_Mesh_init_create: typing.TypeAlias = None | typing.Callable[[_type_Mesh_init_spot], _type_Mesh_init_tile | None]


class Mesh(Mutate):

    """
    A mutate for a collection of tiles.

    :param score:
        Used during searching to determine the order at which each spot's tile should be shown, if at all.
    :param scout:
        Determines whether a spot is valid to move to.
    :param rigid:
        Whether to **not** allow wraping around when moving toward the edge.
    :param create:
        Used for creating tiles for new spots. Can return :code:`None` to prevent creation.
    :param tiles:
        The manipulating tiles.
    :param point:
        The point for the cursor.
    """

    __slots__ = ('_create', '_scout', '_rigid', '_search_score', '_search_mutate', 
                 '_vision', '_search_point_cache', '_clean', '_tiles', '_cursor')

    def __init__(self, 
                 score : _type_Mesh_init_score, 
                 scout : _type_Mesh_init_scout, 
                 rigid : _type_Mesh_init_rigid,
                 create: _type_Mesh_init_create, 
                 clean : _type_Mesh_init_clean,
                 tiles : _type_Mesh_init_tiles, 
                 point : _type_Mesh_init_point,
                 *args, **kwargs):

        self._create = create

        self._scout = scout

        self._rigid = rigid

        search_lines = [[]]

        search_point_y = len(search_lines) - 1
        search_point_x = len(search_lines[search_point_y])
        search_point = [search_point_y, search_point_x]

        self._search_mutate = Text(search_lines, search_point)
        self._search_score = score
        self._vision = {spot: spot for spot in tiles}
        self._search_point_cache = None

        self._clean = clean

        self._tiles = tiles
        
        self._cursor = Cursor(point)

        super().__init__(*args, **kwargs)

        self._insert(self._vis_spot)
    
    @property
    def _search_point(self):

        return self._search_mutate.point
    
    @property
    def search_point(self) -> _type_Mesh_init_spot:

        """
        The search mutate's cursor's point.
        
        Should always be at the end of the :attr:`.search_line`.
        """

        return self._search_point
    
    @property
    def _search_lines(self):

        return self._search_mutate.lines
    
    @property
    def search_lines(self) -> _type_Text_init_lines:

        """
        The search mutate's lines.

        Only one line will be in use at any given time.
        """

        return self._search_lines

    @property
    def _search_line(self):

        return self._search_lines[self._search_point[0]]

    @property
    def search_line(self) -> _type_Text_init_line:

        """
        The search mutate's current line.
        
        Tile creation is only possible when this is empty.
        """

        return self._search_line
    
    @property
    def vision(self) -> dict[_type_Mesh_init_spot, _type_Mesh_init_spot]:

        """
        A mapping of currently visible spots to the real ones they correspond to.
        """

        return self._vision

    @property
    def tiles(self) -> _type_Mesh_init_tiles:

        return self._tiles

    @property
    def _point(self):

        return self._cursor.point

    @property
    def point(self) -> _type_Mesh_init_point:

        """
        The current cursor's point.
        """

        return self._point

    @property
    def _vis_spot(self):

        return tuple(self._point)
    
    @property
    def vis_spot(self) -> _type_Mesh_init_spot:

        """
        The current vision spot. Simply a tuple of :attr:`.point`.
        """

        return self._vis_spot
    
    @property
    def _cur_spot(self):

        spot = self._vision[self._vis_spot]

        return spot
    
    @property
    def cur_spot(self) -> _type_Mesh_init_spot:

        """
        The current real spot, accounting for vision.
        """

        return self._cur_spot
    
    @property   
    def _cur_tile(self):

        return self._tiles[self._cur_spot]
    
    @property
    def cur_tile(self):

        """
        The current tile.
        """

        return self._cur_tile
    
    def _get_state(self):

        tiles = copy.copy(self._tiles)
        
        cursor = self._cursor.get_state()

        search = self._search_mutate.get_state()
        vision = copy.deepcopy(self._vision)

        return self._State(
            tiles = tiles, 
            cursor = cursor, 
            search = search, 
            vision = vision
        )
    
    def _set_state(self, state):

        self._tiles.clear()
        self._tiles.update(state.tiles)
        
        self._cursor.set_state(state.cursor)

        self._search_mutate.set_state(state.search)
        self._vision.clear()
        self._vision.update(state.vision)
    
    def _insert(self, spot):

        if self._search_line:
            raise Error('searching')

        try:
            tile = self._tiles[spot]
        except KeyError:
            pass
        else:
            return tile

        tile = self._create(spot)

        if self._clean:
            self._tiles.clear()
            self._vision.clear()

        if not tile is None:
            self._tiles[spot] = tile
            self._vision[spot] = spot

        return tile
    
    def insert(self, 
               spot: _type_Mesh_init_spot) -> _type_Mesh_init_tile | None:
        
        """
        Attempt to insert a tile.

        :param spot:
            The spot to insert the tile at.

        If one already exists or gets created, it is returned.
        """

        return self._insert(spot)
    
    def _delete(self, spot):

        if self._search_line:
            raise Error('searching')
        
        try:
            tile = self._tiles.pop(spot)
        except KeyError:
            return

        try:
            del self._vision[spot]
        except KeyError:
            pass

        return tile

    def delete(self,
               spot: _type_Mesh_init_spot) -> _type_Mesh_init_tile | None:

        """
        Attempt to delete a tile
        
        :param spot:
            The spot to delete the tile from.
        
        If one exists, it is returned.
        """    

        return self._delete(spot)
    
    def _move(self, direction, size = 1):

        old_spot = self._vis_spot

        fin_spot = None
        if not self._search_line:
            if not self._create is None:
                new_spot = _helpers.get_point_directional_next(old_spot, direction, size)
                if not new_spot in self._tiles:
                    tile = self._insert(new_spot)
                    if not tile is None:
                        fin_spot = new_spot

        if fin_spot is None:
            may_spots = self._vision.keys()
            if not self._scout is None:
                may_spots = filter(self._scout, may_spots) 
            may_spots = tuple(may_spots)
            fin_spot = _helpers.get_point_directional(min, old_spot, direction, may_spots)
            if fin_spot == old_spot:
                if self._rigid:
                    raise Error('insufficient_space', direction = direction)
                direction = _helpers.reverse_direction(direction)
                fin_spot = _helpers.get_point_directional(max, old_spot, direction, may_spots, ignore_point = True)
        
        instructions = enumerate(fin_spot)

        self._cursor.move(instructions)

    def move(self, 
             direction: int):

        """
        Move the cursor to the nearest tile.
         
        :param direction:
            The direction to move toward in circular ``[-90, +180]`` degrees.

        If none exists toward the specified direction, attempt again by wrapping around the other side.
        """

        self._move(direction)

    def _search_execute_setup(self, argument):

        if self._search_point_cache is None:
            self._search_point_cache = copy.copy(self._point)

        assets = []
        for (spot, tile) in self._tiles.items():
            score = self._search_score(argument, tile)
            if score is None:
                continue
            assets.append((score, spot))

        if not assets:
            raise Error('invalid_search_argument', argument = argument)
        
        assets = sorted(assets, reverse = True)
        
        (scores, old_spots) = zip(*assets)

        cur_spots = self._vision.values()

        if set(old_spots) == set(cur_spots):
            raise Error('inconsequential_search_argument', argument = argument)
            
        combos = _helpers.squeeze_spots(0, old_spots)

        self._vision = dict(map(reversed, combos))

        return next(iter(self._vision))

    def _search_execute_reset(self):

        self._vision = {spot: spot for spot in self._tiles}

        point = self._search_point_cache
        self._search_point_cache = None
        
        return point

    def _search_execute(self, function, *args, **kwargs):

        if self._search_score is None:
            return

        argument = self._search_line

        if argument is None:
            return

        state = self._get_state()

        function(*args, **kwargs)

        try:
            if argument:
                point = self._search_execute_setup(argument)
            else:
                point = self._search_execute_reset()
        except Error:
            self._set_state(state)
            raise

        instructions = enumerate(point)

        self._cursor.move(instructions)

    def _search_insert_act(self, runes):

        self._search_mutate.insert(runes)

        size = len(runes)

        self._search_mutate.move_x(size)

    def _search_insert(self, runes):

        self._search_execute(self._search_insert_act, runes)

    def search_insert(self, 
                      runes: list[str]):

        """
        Insert text to the search line, and filter or displace tiles accordingly.

        :param runes:
            The runes to insert.
        """

        self._search_insert(runes)

    def _search_delete_act(self, size):

        self._search_mutate.move_x(- size)
        self._search_mutate.delete(size)

    def _search_delete(self, size):

        self._search_execute(self._search_delete_act, size)

    def search_delete(self, 
                      size: int):

        """
        Delete from the search line, and filter or displace tiles accordingly.

        :param size:
            The amount of runes to delete.
        """

        self._search_delete(size)