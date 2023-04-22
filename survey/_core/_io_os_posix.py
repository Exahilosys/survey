import termios

from . import _io_os


__all__ = ('IO',)


class IO(_io_os.StreamIO):

    __slots__ = ('_i_fd',)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._i_fd = self._i.fileno()

    def _wait(self, mode, switch):

        mode[6][termios.VMIN] = 1 if switch else 0

        return mode

    def _init(self):

        save = termios.tcgetattr(self._i_fd)

        mode = termios.tcgetattr(self._i_fd)

        mode[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON)
        mode[6][termios.VTIME] = 0

        return (save, mode)

    def _set(self, mode):

        termios.tcsetattr(self._i_fd, termios.TCSAFLUSH, mode)
