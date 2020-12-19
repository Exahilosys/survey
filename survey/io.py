import os

from . import helpers


__all__ = ('IO',)


class BaseIO:

    __slots__ = ('_i', '_o', '_buffer')

    def __init__(self, i, o):

        self._i = i
        self._o = o

        self._buffer = []

    def feed(self, data):

        self._buffer.extend(data)

    def _send(self, value):

        raise NotImplementedError()

    def send(self, value):

        self._send(value)

    def _recv(self):

        raise NotImplementedError()

    def recv(self):

        try:
            rune = self._buffer.pop(0)
        except IndexError:
            rune = self._recv()

        return rune

    def ring(self):


        self._send('\a')


class ModeIO(BaseIO):

    __slots__ = ('_atomic', '_i_save', '_i_mode')

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._atomic = helpers.Atomic(self.start, self.stop)

    @property
    def atomic(self):

        return self._atomic

    def _init(self):

        raise NotImplementedError()

    def _swap(self, mode):

        raise NotImplementedError()

    def start(self):

        (self._i_save, mode) = self._init()

        self._swap(mode)

        self._i_mode = mode

    def stop(self):

        self._swap(self._i_save)

        self._i_save = None


class StreamModeIO(ModeIO):

    __slots__ = ()

    def _send(self, value):

        self._o.write(value)
        self._o.flush()

    def _recv(self):

        rune = self._i.read(1)

        return rune

    def setup(self):

        pass

    def reset(self):

        pass


if os.name == 'nt':

    import msvcrt
    import ctypes
    import ctypes.wintypes

    _kernel32 = ctypes.windll.kernel32

    class IO(StreamModeIO):

        __slots__ = ('_i_fh', '_o_fh', '_o_save')

        def __init__(self, *args, **kwargs):

            super().__init__(*args, **kwargs)

            i_fd = self._i.fileno()
            self._i_fh = msvcrt.get_osfhandle(i_fd)

            o_fd = self._o.fileno()
            self._o_fh = msvcrt.get_osfhandle(o_fd)

        def _getm(self, fh):

            c_mode = ctypes.wintypes.DWORD()

            _kernel32.GetConsoleMode(fh, ctypes.byref(c_mode))

            mode = c_mode.value

            return mode

        def _init(self):

            save = self._getm(self._i_fh)

            mode = save &~ (2 | 4 | 32) | 512
            # - (ENABLE_LINE_INPUT + ENABLE_ECHO_INPUT + ENABLE_INSERT_MODE)
            # + ENABLE_VIRTUAL_TERMINAL_INPUT

            return (save, mode)

        def _setm(self, fh, mode):

            c_mode = ctypes.wintypes.DWORD(mode)

            _kernel32.SetConsoleMode(fh, c_mode)

        def _swap(self, mode):

            self._setm(self._i_fh, mode)

        def setup(self):

            mode = self._o_save = self._getm(self._o_fh)

            mode = mode | 1 | 4
            # + ENABLE_PROCESSED_OUTPUT + ENABLE_VIRTUAL_TERMINAL_PROCESSING

            self._setm(self._o_fh, mode)

        def reset(self):

            self._setm(self._o_fh, self._o_save)

else:

    import termios

    class IO(StreamModeIO):

        __slots__ = ('_i_fd',)

        def __init__(self, *args, **kwargs):

            super().__init__(*args, **kwargs)

            self._i_fd = self._i.fileno()

        def _init(self):

            save = termios.tcgetattr(self._i_fd)

            mode = termios.tcgetattr(self._i_fd)

            mode[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON)
            mode[6][termios.VTIME] = 0
            mode[6][termios.VMIN] = 1

            return (save, mode)

        def _swap(self, mode):

            termios.tcsetattr(self._i_fd, termios.TCSAFLUSH, mode)
