import typing
import enum
import threading

from . import _helpers
from . import _ansi
from . import _io


__all__ = ('ClearMode', 'EraseMode', 'Cursor')


class ClearMode(enum.IntEnum):

    """
    ClearMode()
    
    Denotes how the cursor clears the screen.
    """

    #: Clear all runes right-and-down of the cursor.
    right  = 0
    #: Clear all runes left-and-up of the cursor.
    left   = 1
    #: Clear all runes.
    full   = 2
    #: Clear all runes and delete scrollback lines.
    extend = 3


class EraseMode(enum.IntEnum):

    """
    EraseMode()
    
    Denotes how the cursor erases the line.
    """

    #: Erase all visible runes right of the cursor.
    right  = 0
    #: Erase all visible runes left of the cursor.
    left   = 1
    #: Erase all visible runes.
    full   = 2


class Cursor:

    """
    Emulates the on-screen cursor.

    .. note::

        Coordinates here are ``1``-offset indexes, meaning they start from 1. 
        The position of the cursor on the top-left-most of the screen is :code:`(1, 1)`.
        
    :param io:
        Used for sending ANSI sequences to output.

    .. code-block:: python
    
        io = IO(sys.stdin, sys.stdout)
        cursor = Cursor(io)
        location = cursor.locate()
    """

    __slots__ = ('_lock', '_hidden', '_io')

    def __init__(self, 
                 io: _io.IO):

        self._io = io

        self._hidden = _helpers.Atomic(self.hide, self.show)

        self._lock = threading.RLock()

    @property
    def hidden(self):

        """
        A context manager for hiding the cursor.

        .. code-block:: python

            with cursor.hidden:
                ...
        """

        return self._hidden

    @_helpers.ctxmethod(lambda self: self._io)
    def _send(self, *args, escape = False, **kwargs):

        function = _ansi.get_escape if escape else _ansi.get_control

        value = function(*args, **kwargs)

        self._io.send(value)

    def _up(self, size):

        self._send('A', size)

    def up(self, size: int | None = None):

        """
        Move up. No effect if at the edge of the screen.

        :param size:
            The amount of lines to move by. System default  is usually :code:`1`.
        """

        self._up(size)

    def _down(self, size):

        self._send('B', size)

    def down(self, size: int | None = None):

        """
        Move down. No effect if at the edge of the screen.

        :param size:
            The amount of lines to move by. System default  is usually :code:`1`.
        """

        self._down(size)

    def _left(self, size):

        self._send('D', size)

    def left(self, size: int | None = None):

        """
        Move left. No effect if at the edge of the screen.

        :param size:
            The amount of lines to move by. System default  is usually :code:`1`.
        """

        self._left(size)

    def _right(self, size):

        self._send('C', size)

    def right(self, size: int | None = None):

        """
        Move right. No effect if at the edge of the screen.

        :param size:
            The amount of lines to move by. System default  is usually :code:`1`.
        """

        self._right(size)

    def _goto(self, x):

        self._send('G', x)

    def goto(self, x: int = None):

        """
        Move absolutely on line.

        :param x:
            The absolute coordinate to move to. System default  is usually :code:`1`.
        """

        self._goto(x)

    def _last(self, size):

        self._send('F', size)

    def last(self, size: int | None = None):

        """
        Move up at line start.

        :param size:
            The amount of lines to move by. System default  is usually :code:`1`.
        """

        self._last(size)

    def _next(self, size):

        self._send('E', size)

    def next(self, size: int | None = None):

        """
        Move down at line start.

        :param size:
            The amount of lines to move by. System default  is usually :code:`1`.
        """

        self._next(size)

    def _move(self, y, x):

        self._send('f', y, x)

    def move(self, y: int | None = None, x: int | None = None):

        """
        Move absolutely on screen.

        :param y:
            The absolute vertical coordinate to move to. System default  is usually :code:`1`.
        :param x:
            The absolute horizontal coordiante to move to. System default  is usually :code:`1`.
        """
        
        self._move(y, x)

    def _clear(self, mode):

        self._send('J', mode)

    def clear(self, mode: ClearMode = None):

        """
        Clear the screen.

        :param mode:
            Denotes which part of the screen to clear. System default  is usually :attr:`ClearMode.right`.
        """

        self._clear(mode)

    def _erase(self, mode):

        self._send('K', mode)

    def erase(self, mode: EraseMode = None):

        """
        Erase the line.

        :param mode:
            Denotes which part of the screen to clear. System default  is usually :attr:`EraseMode.right`.
        """

        self._erase(mode)

    def _save(self):

        self._send('7', escape = True)

    def save(self):

        """
        Save the current position. Consequent uses will overwrite previous ones.
        """

        self._save()

    def _load(self):

        self._send('8', escape = True)

    def load(self):

        """
        Move to the last-saved position. Consequent uses will have the same result.
        """

        self._load()

    def _hide(self):

        self._send('l', '25', private = True)

    def hide(self):

        """
        Become invisible.
        """

        self._hide()

    def _show(self):

        self._send('h', '25', private = True)

    def show(self):

        """
        Become visible.
        """

        self._show()

    @_helpers.ctxmethod(lambda self: self._lock)
    @_helpers.ctxmethod(lambda self: self._io)
    def _locate(self):

        self._send('n', '6')
        
        while True:
            code = _ansi.parse(self._io.recv)
            if not isinstance(code, _ansi.Sequence) and code.rune == 'R':
                continue
            break

        point = tuple(map(int, code.args))

        return point

    def locate(self) -> tuple[int, int]:

        """
        Get the current absolute vertical and horizontal coordinates.

        :returns:
            ``(vertical, horizontal)``
        """

        point = self._locate()

        return point

    _max_y = _max_x = 9999

    @_helpers.ctxmethod(lambda self: self._lock)
    def _measure(self):

        self._save()

        self._move(self._max_y, self._max_x)

        point = self._locate()

        self._load()

        return point

    def measure(self) -> tuple[int, int]:

        """
        Get the maximum possible vertical and horizontal coordinates.

        :returns:
            ``(vertical, horizontal)``
        """

        with self._hidden:
            point = self._measure()

        return point