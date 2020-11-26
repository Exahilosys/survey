import termios

from . import helpers


__all__ = ('IO',)


class IO:

    __slots__ = ('_i', '_o', '_buffer', '_fd', '_save', '_mode', '_block',
                 '_atomic')

    def __init__(self, i, o):

        self._i = i
        self._o = o

        self._buffer = []

        self._fd = i.fileno()

        self._save = None
        self._mode = None

        self._block = None

        self._atomic = helpers.Atomic(self.start, self.stop)

    @property
    def atomic(self):

        return self._atomic

    def _swap(self, mode):

        termios.tcsetattr(self._fd, termios.TCSAFLUSH, mode)

    def _fix(self, block):

        self._block = block

        self._mode[6][termios.VMIN] = int(block)

        self._swap(self._mode)

    def start(self):

        """
        Save settings and enter cbreak mode.
        """

        self._save = termios.tcgetattr(self._fd)

        mode = termios.tcgetattr(self._fd)

        mode[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON)
        mode[6][termios.VTIME] = 0

        self._mode = mode

        self._fix(True)

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

    def recv(self, block = True):

        """
        Read from input buffer.
        """

        if not block is self._block:
            self._fix(block)

        try:
            return self._buffer.pop(0)
        except IndexError:
            pass

        return self._i.read(1)

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
