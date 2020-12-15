import termios

from . import helpers


__all__ = ('IO',)


class IO:

    __slots__ = ('_i', '_o', '_buffer', '_fd', '_save', '_mode', '_atomic')

    def __init__(self, i, o):

        self._i = i
        self._o = o

        self._buffer = []

        self._fd = i.fileno()

        self._save = None
        self._mode = None

        self._atomic = helpers.Atomic(self.start, self.stop)

    @property
    def atomic(self):

        return self._atomic

    def _swap(self, mode):

        termios.tcsetattr(self._fd, termios.TCSAFLUSH, mode)

    def start(self):

        """
        Save settings and enter cbreak mode.
        """

        self._save = termios.tcgetattr(self._fd)

        mode = termios.tcgetattr(self._fd)

        mode[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON)
        mode[6][termios.VTIME] = 0
        mode[6][termios.VMIN] = 1

        self._swap(mode)

        self._mode = mode

    def stop(self):

        """
        Restore initial settings.
        """

        self._swap(self._save)

        self._save = None

    def send(self, value):

        """
        Write to output buffer.
        """

        self._o.write(value)
        self._o.flush()

    def recv(self):

        """
        Read from input buffer.
        """

        try:
            rune = self._buffer.pop(0)
        except IndexError:
            rune = self._i.read(1)

        return rune

    def feed(self, data):

        """
        Funnel additional data to be read before input buffer.
        """

        self._buffer.extend(data)

    def ring(self):

        """
        Sound system bell.
        """

        self.send('\a')
