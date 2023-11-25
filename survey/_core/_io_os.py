
from . import _helpers


__all__ = ('BaseIO', 'ModeIO', 'StreamIO')


class BaseIO:

    __slots__ = ('_i', '_o')

    def __init__(self, i, o):

        self._i = i
        self._o = o

    def _send(self, text):

        raise NotImplementedError()

    def send(self, 
             text: str):

        """
        Send text to the output.

        :param text:
            The text to send.
        """

        self._send(text)

    def _recv(self):

        raise NotImplementedError()

    def recv(self) -> str:

        """
        Wait and receive text from the input.
        """

        text = self._recv()

        return text


class ModeIO(BaseIO):

    __slots__ = ('_atomic', '_i_save', '_i_mode')

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._atomic = _helpers.Atomic(self._start, self._stop)
        
    def _init(self):

        raise NotImplementedError()

    def _set(self, mode):

        raise NotImplementedError()

    def _wait(self, mode, switch):

        raise NotImplementedError()

    def wait(self, 
             switch: bool):

        """
        Change the receiving mode waiting behavior.
        """

        mode = self._wait(self._i_mode, switch)

        self._set(mode)

    def _start(self):

        self._i_save, mode = self._init()

        mode = self._wait(mode, True)

        self._set(mode)

        self._i_mode = mode

    def _stop(self):

        self._set(self._i_save)

        self._i_save = None

    @property
    def __enter__(self):

        return self._atomic.__enter__

    @property
    def __exit__(self):

        return self._atomic.__exit__


class StreamIO(ModeIO):

    __slots__ = ()

    def _send(self, value):

        self._o.write(value)
        self._o.flush()

    def _recv(self):

        text = self._i.read1()

        return text

    def __iter__(self):

        while not self._i.closed:
            yield self._recv()
