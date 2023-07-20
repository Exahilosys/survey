import itertools

from . import _helpers
from . import _ansi
from . import _io


__all__ = ('Intel',)


class _EmptyRead(Exception):

    __slots__ = ()


_check_any = lambda *args, **kwargs: True


class Intel:

    def __init__(self, 
                 io: _io.IO):

        self._io = io

        self._rune_buffer = []
        self._code_buffer = []

    def _fill_text(self):

        if self._rune_buffer:
            return
        
        text = self._io.recv()

        if text == '\x1b':
            return

        self._rune_buffer.extend(text)

    def _read_text(self):

        self._fill_text()

        try:
            rune = self._rune_buffer.pop(0)
        except IndexError:
            raise _EmptyRead()

        return rune
    
    _empty = _ansi.Escape('')
    
    def _fill_code(self):
        
        try:
            code = _ansi.parse(self._read_text)
        except _EmptyRead:
            code = self._empty

        self._code_buffer.append(code)
    
    @_helpers.ctxmethod(lambda self: self._io)
    def _read_code(self, check):

        if check is None:
            check = _check_any

        for index in itertools.count(0):
            for _ in range(2):
                try:
                    code = self._code_buffer[index]
                except IndexError:
                    self._fill_code()
                else:
                    break
            if check(code):
                break
            index += 1

        del self._code_buffer[index]
        
        return code
    
    def _read(self, check):

        code = self._read_code(check)

        return code
    
    def read(self, check = None):

        return self._read(check)
    
    def _send(self, text):

        self._io.send(text)

    def send(self, text):

        self._send(text)
