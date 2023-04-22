import typing
import threading

from . import _helpers
from . import _cursor
from . import _render


__all__ = ('Screen',)


_type_Screen_draw_sketch: typing.TypeAlias = typing.Callable[[], tuple[_render._type_Render_draw_lines, _render._type_Render_draw_point]]


class Screen:

    """
    Encapsulates the visualization logic.

    :param render:
        Used for drawing and cursor placement.
    :param cursor:
        Used for hidding the cursor between draws.
    """

    __slots__ = ('_cursor', '_render', '_lock')

    def __init__(self, 
                 render: _render.Render, 
                 cursor: _cursor.Cursor):

        self._cursor = cursor
        self._render = render

        self._lock = threading.Lock()

    @_helpers.ctxmethod(lambda self: self._lock)
    @_helpers.ctxmethod(lambda self: self._cursor.hidden)
    def _print(self, sketch, re, **kwargs):

        if re:
            self._render.back()

        info = sketch()

        self._render.draw(*info, **kwargs)

    def print(self, 
              sketch: _type_Screen_draw_sketch,
              re: bool,
              *,
              clean: bool = True,
              learn: bool = True):
        
        """
        Fetch drawing information and use it to print.

        :param sketch:
            Used after potentially placing the cursor to its initial position. Should return ``(lines, point)`` used for drawing.
        :param re:
            Whether to return the cursor to its initial position before attempting to draw.
        :param clean:
            Same as :paramref:`.Render.draw.clean`.
        :param learn:
            Same as :paramref:`.Render.draw.learn`.

        The reason a callable is required instead of ``(lines, point)``, is to allow the original cursor information to be true on every call.
        """
        
        self._print(sketch, re, clean = clean, learn = learn)


