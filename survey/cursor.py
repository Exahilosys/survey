import types
import re

from . import helpers


__all__ = ('Cursor',)


_CSI = '\x1b'


ClearMode = types.SimpleNamespace(right = 0, left = 1, full = 2, extend = 3)


EraseMode = types.SimpleNamespace(right = 0, left = 1, full = 2)


class Cursor:

    __slots__ = ('_io', '_hidden')

    def __init__(self, io):

        self._io = io

        self._hidden = helpers.Atomic(self.hide, self.show)

    @property
    def hidden(self):

        return self._hidden

    def _send(self, code, *args, private = False):

        check = lambda value: not value is None
        params = ';'.join(map(str, filter(check, args)))
        if args:
            params = '[' + params

        self._io.send(_CSI + params + code)

    def up(self, size = None):

        """
        Move `size` cells up.
        """

        if size == 0:
            return

        self._send('A', size)

    def down(self, size = None):

        """
        Move `size` cells down.
        """

        if size == 0:
            return

        self._send('B', size)

    def left(self, size = None):

        """
        Move `size` cells left.
        """

        if size == 0:
            return

        self._send('D', size)

    def right(self, size = None):

        """
        Move `size` cells right.
        """

        if size == 0:
            return

        self._send('C', size)

    def goto(self, x = None):

        """
        Move to `x` column.
        """

        self._send('G', x)

    def next(self, size = None):

        """
        Move to beginning of `size` lines down.
        """

        if size == 0:
            self.goto(0)
            return

        self._send('E', size)

    def last(self, size = None):

        """
        Move to beginning of `size` lines up.
        """

        if size == 0:
            self.goto(0)
            return

        self._send('F', size)

    def move(self, y, x):

        """
        Move to `x` and `y` coordinates:
        """

        self._send('f', y, x)

    def clear(self, mode = None):

        """
        Clear display.
        """

        self._send('J', mode)

    def erase(self, mode = None):

        """
        Erase in-line.
        """

        self._send('K', mode)

    def save(self):

        """
        Save current location.
        """

        self._send('7')

    def load(self):

        """
        Move to saved location.
        """

        self._send('8')

    def show(self):

        """
        Show.
        """

        self._send('h', '?25')

    def hide(self):

        """
        Hide.
        """

        self._send('l', '?25')

    def _locate(self, pattern = re.compile(_CSI + '\[(\d+);(\d+)R$')):

        buffer = ''
        funnel = []

        self._send('n', '6')

        while True:
            rune = self._io.recv()
            buffer += rune
            if rune == 'R':
                index = buffer.rindex(_CSI)
                portion = buffer[index:]
                match = pattern.match(portion)
                if match:
                    break
                else:
                    funnel.extend(buffer)

        groups = match.groups()
        values = (groups[index] for index in range(2))

        return tuple(map(int, values))

    def locate(self):

        """
        Get current location.
        """

        with self._io.atomic:
            result = self._locate()

        return result

    def measure(self):

        """
        Get screen size.
        """

        self.save()

        with self._hidden:
            self.move(999, 9999)
            size = self.locate()
            self.load()

        return size
