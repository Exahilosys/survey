import typing

from . import _helpers
from . import _io
from . import _ansi
from . import _source


__all__ = ('Terminate', 'Handle')


class Terminate(Exception):

    """
    Signals the invokation loop to stop.
    """


_type_Handle_start_invoke: typing.TypeAlias = typing.Callable[[str, _ansi._type_parse_return], None]

    
class Handle:

    """
    Encapsulates the invokation loop logic.
    """

    __slots__ = ('_io',)

    def __init__(self, 
                 io: _io.IO):

        self._io = io

    @_helpers.ctxmethod(lambda self: self._io)
    def _start(self, invoke):

        source = _source.Source(invoke, self._io)

        try:
            source.listen()
        except Terminate:
            pass

    def start(self,
              invoke: _type_Handle_start_invoke):
        
        """
        Start the invokation loop.

        This will use :meth:`.Source.listen` until :exc:`Terminate` is raised.

        :param invoke:
            Used as :paramref:`.Source.callback` callback.
        """

        self._start(invoke)