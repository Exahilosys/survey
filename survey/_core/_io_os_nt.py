import msvcrt
import ctypes
import ctypes.wintypes

from . import _constants
from . import _io_os


__all__ = ('IO',)


_LINESEP = _constants.linesep.encode()


def _recv_linesep(text):

    return _LINESEP


def _recv_interrupt(text):

    raise KeyboardInterrupt


class IO(_io_os.StreamIO):

    __slots__ = ('_i_fh', '_o_fh', '_o_save')

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        i_fd = self._i.fileno()
        self._i_fh = msvcrt.get_osfhandle(i_fd)

        o_fd = self._o.fileno()
        self._o_fh = msvcrt.get_osfhandle(o_fd)

    def _wait(self, mode, switch):

        bit = 2

        if switch:
            # - ENABLE_LINE_INPUT
            mode &= ~ bit
        else:
            # + ENABLE_LINE_INPUT
            mode |= bit

        return mode

    @staticmethod
    def _getm(fh):

        c_mode = ctypes.wintypes.DWORD()

        ctypes.windll.kernel32.GetConsoleMode(fh, ctypes.byref(c_mode))

        mode = c_mode.value

        return mode

    def _init(self):

        save = self._getm(self._i_fh)

        # - ENABLE_PROCESSED_INPUT
        # - ENABLE_ECHO_INPUT
        # - ENABLE_INSERT_MODE
        # + ENABLE_VIRTUAL_TERMINAL_INPUT
        mode = save &~ (1 | 4 | 32) | 512

        return (save, mode)

    @staticmethod
    def _setm(fh, mode):

        c_mode = ctypes.wintypes.DWORD(mode)

        ctypes.windll.kernel32.SetConsoleMode(fh, c_mode)

    def _set(self, mode):

        self._setm(self._i_fh, mode)

    def _setup(self):

        mode = self._o_save = self._getm(self._o_fh)

        # + ENABLE_PROCESSED_OUTPUT
        # + ENABLE_VIRTUAL_TERMINAL_PROCESSING
        mode = mode | 1 | 4

        self._setm(self._o_fh, mode)

    def _reset(self):

        self._setm(self._o_fh, self._o_save)

    _recv_replace = {
        b'\r': _recv_linesep,
        b'\x03': _recv_interrupt
    }

    def _recv(self):

        text = super()._recv()

        while True:
            try:
                function = self._recv_replace[text]
            except KeyError:
                break
            else:
                text = function(text)
        
        return text

    def __enter__(self, *args):

        self._setup()

        return super().__enter__(*args)

    def __exit__(self, *args):

        self._reset()

        return super().__exit__(*args)