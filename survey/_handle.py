
"""
Handling incoming events and their information by delegating to functions that can handle them.
"""

import typing
import enum

from . import _helpers
from . import _core
from . import _controls


__all__ = ('EventType', 'Abort', 'Handle')


class EventType(enum.StrEnum):

    """
    Flags whether the event is called back before or after invokation.
    """

    enter = 'enter'
    leave = 'leave'


class Abort(Exception):

    """
    Can be raised during a callback with :attr:`EventType.enter` to prevent invokation.
    """

    __slots__ = ()


_type_Handle_init_unsafe  : typing.TypeAlias = bool
_type_Handle_init_callback: typing.TypeAlias = typing.Callable[[tuple[EventType, _core.Event], _core._type_ansi_parse_return], None]

_type_Handle_add_control  : typing.TypeAlias = _controls.Control

_type_Handle_invoke_event : typing.TypeAlias = _core.Event


class Handle:

    """
    Used for holding and calling "control" functions that determine action for each :class:`._core.Event`.

    :param unsafe:
        Whether :exc:`KeyError` should be surfaced when an invoke is missing.
    :param callback:
        Called before and after invokation with :attr:`.Event.enter.` and :attr:`.Event.leave` prepended in the arguments respectively.
    """

    __slots__ = ('_args', '_unsafe', '_controls', '_callback')

    def __init__(self, 
                 *args,
                 unsafe  : _type_Handle_init_unsafe   = False, 
                 callback: _type_Handle_init_callback = None):

        self._args = args
        self._unsafe = unsafe
        self._controls = {}
        self._callback = callback or _helpers.noop

    def add(self, 
            control: _type_Handle_add_control):

        """
        Add a control.
        """

        self._controls[control.event] = control

    def _dispatch(self, type, name, *args):
        
        event = (type, name)

        self._callback(event, *args)

    def invoke(self, 
               event: _type_Handle_invoke_event, 
               *args):

        """
        Invoke a control if it exists.
        """

        try:
            control = self._controls[event]
        except KeyError:
            if self._unsafe:
                raise
            return
        
        try:
            self._dispatch(EventType.enter, event, *args)
        except Abort:
            return

        control.function(*self._args, *args)

        self._dispatch(EventType.leave, event, *args)


        
        