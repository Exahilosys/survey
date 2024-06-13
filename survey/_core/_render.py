import typing
import math
import functools
import dataclasses
import threading
import weakref
import unicodedata

from . import _helpers
from . import _constants
from . import _ansi
from . import _cursor
from . import _intel


__all__ = ('Render',)


def _get_line_wrap_y(limit: int, 
                     size: int):

    """
    Get the amount of y-space needed to render a line in a given x-space.

    :param limit:
        The x-space limit.
    :param size:
        The size of the line.

    .. code-block:: python

        _get_line_wrap_y(5, 8 ) # 2
        _get_line_wrap_y(9, 4 ) # 1
        _get_line_wrap_y(5, 33) # 7
    """

    return math.floor(size / limit) + 1


def _get_line_wrap_y_sum(limit: int, 
                         sizes: typing.List[int]):

    """
    Get the amount of y-space needed to render a list of lines in a given x-space.

    :param limit:
        The x-space limit.
    :param size:
        The size of the line.

    .. code-block:: python

        _get_line_wrap_y(5, (8, 4)) # 3
        _get_line_wrap_y(9, (4, 2)) # 2
        _get_line_wrap_y(5, (6, 9)) # 4
    """

    get = functools.partial(_get_line_wrap_y, limit)

    return sum(map(get, sizes))


def _get_point_wrap(limit: int, 
                    sizes: typing.List[int], 
                    cur_y: int, 
                    cur_x: int):

    """
    Get the (y, x) in a list of lines after accounting for a given x-space.
    """

    req_x = _get_line_wrap_y(limit, cur_x)

    usr_y = _get_line_wrap_y_sum(limit, sizes[:cur_y]) + req_x
    usr_x = cur_x - (req_x - 1) * limit

    # turn to index via count
    usr_y -= 1

    return (usr_y, usr_x)


class Memory:

    __slots__ = ('y', 'x', '__weakref__')

    def __init__(self, y, x):

        self.y = y
        self.x = x
    

_type_Render_draw_lines = typing.List[typing.List[str]]
_type_Render_draw_point = typing.Union[typing.List[int], None]


class Render:

    """
    Assists with printing text in a predictible way.

    .. note::
        In contrast to how :class:`.Cursor` works, point coordinates here are 0-offset indexes.
    
    :param cursor:
        Used for moving and clearing.
    :param intel:
        Used for sending to the output.

    .. code-block:: python
    
        io = IO(sys.stdin, sys.stdout)
        intel = Intel(io)
        cursor = Cursor(intel)
        render = Render(cursor, intel)
        # draw "Hello\\nWorld" and place cursor between "r" and "l".
        render.draw([['H', 'e', 'l', 'l', 'o'], ['W', 'o', 'r', 'l', 'd']], [1, 3])
    """

    _history = weakref.WeakSet()

    _style_reset = _ansi.get_control('m', 0)

    __slots__ = ('_cursor', '_memory', '_lock')

    def __init__(self,
                 cursor: _cursor.Cursor):

        self._cursor = cursor
        self._memory = None
        
        self._lock = threading.Lock()
    
    @property
    def cursor(self) -> _cursor.Cursor:

        """
        The cursor used for positioning the cursor and fetching coordinate information.
        """

        return self._cursor

    @property
    def memory(self) -> _type_Render_draw_point:

        """
        The last initial cursor position.
        """

        return self._memory
    
    def _send_direct(self, text):

        self._cursor.intel.io.send(text)

    def _send(self, clean, lines):

        for index, line in enumerate(lines):
            if index:
                self._send_direct(_constants.linesep)
            text = ''.join(line)
            self._send_direct(text)
            if clean:
                self._cursor.erase()

    def _move(self, sizes, cur_y, cur_x, max_x, point):

        usr_y, usr_x = point

        usr_x += cur_x if usr_y == 0 else 1

        usr_y, usr_x = _get_point_wrap(max_x, sizes, usr_y, usr_x)

        usr_y += cur_y
        
        self._cursor.move(usr_y, usr_x)

    @_helpers.ctxmethod(lambda self: self._lock)
    def _draw(self, learn, clean, lines, point):

        lines = tuple(map(tuple, lines))

        cur_y, cur_x = self._cursor.locate()
        max_y, max_x = self._cursor.measure()

        if not point is None:
            for rune in lines[point[0]][:point[1]]:
                try:
                    iuni = unicodedata.east_asian_width(rune)
                except TypeError:
                    continue
                cur_x += iuni in ('W', 'A', 'F')

        memory = Memory(cur_y, cur_x)

        if learn:
            self._memory = memory
            self._history.add(memory)

        self._send_direct(self._style_reset)

        self._send(True, lines)

        if clean:
            self._cursor.clear()

        sizes = list(map(len, lines))

        # adjust initial x
        sizes[0] += cur_x - 1

        # total y needed
        tot_y = _get_line_wrap_y_sum(max_x, sizes)
        # total y remaining 
        got_y = max_y - cur_y
        # total y generated
        ext_y = tot_y - got_y
        # might have enough
        ext_y = max(0, ext_y - 1)

        for oth_memory in self._history:
            # adjust extra y
            oth_memory.y -= ext_y

        if not point is None:
            # "memory" from loop above
            self._move(sizes, memory.y, memory.x, max_x, point)

    def draw(self, 
             lines: _type_Render_draw_lines,
             point: _type_Render_draw_point = None,
             *,
             clean: bool = True,
             learn: bool = True):

        """
        Draw lines and place the cursor among them.

        :param lines:
            The lines to draw.
        :param point:
            The coordiantes among the lines to place the cursor.
        :param clean:
            Whether to clear the rest of the screen after drawing the lines.
        :param learn:
            Whether to keep track of the initial cursor position.
        """

        self._draw(learn, clean, lines, point)

    def _back(self):

        memory = self._memory

        if memory is None:
            return
        
        self._cursor.move(memory.y, memory.x)

        self._memory = None

    def back(self):

        """
        Move the cursor to the position it was before drawing.
        """

        self._back()


