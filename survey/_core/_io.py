import io

from . import _helpers


__all__ = ('IO',)


_system_module = _helpers.import_module_os('_io')


class BaseIO(_system_module.IO):

    __slots__ = ()

    def _ring(self):

        super()._send(b'\a')

    def ring(self):

        """
        Trigger the system's bell.
        """

        return self._ring()


class IO(BaseIO):

    """
    Manages the input and output buffers.

    .. code-block::

        io = IO(sys.stdin, sys.stdout)

        with io: 
            rune = io.recv()
            io.send('You pressed ' + rune)
    """

    __slots__ = ('_i_encoding', '_o_encoding')

    def __init__(self, 
                 i: io.TextIOWrapper, 
                 o: io.TextIOWrapper, 
                 *args, **kwargs):

        self._i_encoding = i.encoding
        self._o_encoding = o.encoding

        super().__init__(i.buffer, o.buffer, *args, **kwargs)

    def _encode(self, text):

        return text.encode(self._o_encoding)

    def _send(self, 
              text: str):

        text_raw = self._encode(text)

        super()._send(text_raw)

    def _decode(self, text):

        return text.decode(self._i_encoding)

    def _recv(self) -> str:

        text_raw = super()._recv()

        text = self._decode(text_raw)

        return text

    def __iter__(self):

        iterable = super().__iter__()

        yield from map(self._decode, iterable) 
