import typing

from . import _screen
from . import _render
from . import _handle
from . import _io
from . import _cursor
from . import _ansi


__all__ = ('SkipDraw', 'Console')


class SkipDraw(Exception):

    """
    Signals the invokation loop to not skip drawing for the current turn.
    """

    __slots__ = ()


class Console:

    """
    Standardizes interaction with the IO into a wait-receive-invoke loop.

    :param handle:
        Used for the invokation loop.
    :param screen:
        Used for visualizing.
    """

    __slots__ = ('_handle', '_screen')

    def __init__(self, 
                 handle: _handle.Handle, 
                 screen: _screen.Screen):

        self._handle = handle
        self._screen = screen

    @property
    def handle(self) -> _handle.Handle:

        """
        The internal handle.
        """

        return self._handle
    
    @property
    def screen(self) -> _screen.Screen:

        return self._screen
    
    def _start(self, sketch, invoke):
        
        def print(re):
            self._screen.print(sketch, re)

        def callback(name, info):
            try:
                invoke(name, info)
            except SkipDraw:
                return
            print(True)

        print(False)

        self._handle.start(callback)

    def start(self,
              sketch: _screen._type_Screen_draw_sketch, 
              invoke: _handle._type_Handle_start_invoke):
        
        """
        Creates an invokation-visualization loop. 
        
        1. ``sketch`` is used for the initial print.
        2. ``invoke`` is used once input is received. 
        3. ``sketch`` is used for the updated print.
        4. Repeat from step **2** until :exc:`.handle.Terminate` gets raised.

        :param sketch:
            Used for visualizing.
        :param invoke:
            Called upon receiving info from the IO.
        """
        
        self._start(sketch, invoke)