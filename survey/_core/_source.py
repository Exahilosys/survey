import typing
import enum
import threading

from . import _helpers
from . import _ansi
from . import _intel


__all__ = ('Source', 'Event')


class EventType(enum.Enum):

    none     = None
    text     = _ansi.Text
    control  = _ansi.Control
    escape   = _ansi.Escape
    sequence = _ansi.Sequence


class Event(str, enum.Enum):

    """
    Event()

    Names for received events.
    """

    #: 
    insert       = 'insert'
    #: 
    arrow_left   = 'arrow_left'
    #: 
    arrow_right  = 'arrow_right'
    #: 
    arrow_up     = 'arrow_up'
    #: 
    arrow_down   = 'arrow_down'
    #: 
    delete_left  = 'delete_left'
    #: 
    delete_right = 'delete_right'
    #: 
    escape       = 'escape'
    #: 
    indent       = 'indent'
    #: 
    enter        = 'enter'


class _EmptyRead(Exception):

    __slots__ = ()


_type_Source_init_callback = typing.Callable[[Event, _ansi._type_parse_return], None]


class Source:

    """
    Translates incoming ANSI sequences to events and calls back with relevant information.

    :param callback:
        Called with ``(name, info)`` upon receiving and translating.
    :param intel:
        Used for receiving from input.
    """

    __slots__ = ('_callback', '_intel', '_lock')

    def __init__(self, 
                 callback: _type_Source_init_callback, 
                 intel   : _intel.Intel):

        self._callback = callback
        self._intel = intel

        self._lock = threading.RLock()

    _group = {
        EventType.control: {
            '\x7f': Event.delete_left,
            '\x08': Event.delete_right,
            '\x0d': Event.enter,
            '\x09': Event.indent
        },
        EventType.escape: {
            '': Event.escape
        },
        EventType.sequence: {
            'A': Event.arrow_up,
            'B': Event.arrow_down,
            'D': Event.arrow_left,
            'C': Event.arrow_right
        }
    }

    _mimic = {
        EventType.control: {
            '\n': _ansi.parse_iterable('\x0d')
        },
        EventType.escape: {
            'f': _ansi.parse_iterable('\x1b[1;3C'),
            'b': _ansi.parse_iterable('\x1b[1;3D')
        },
        EventType.sequence: {
            '~': _ansi.parse_iterable('\x08')
        }
    }

    def _process(self, info):

        while True:
            type = EventType(info.__class__)
            try:
                info = self._mimic[type][info.rune]
            except KeyError:
                break

        try:
            names = self._group[type]
        except KeyError:
            name = Event.insert
        else:
            try:
                name = names[info.rune]
            except KeyError:
                return
        
        self._callback(name, info)

    @_helpers.ctxmethod(lambda self: self._lock)
    def _advance(self):

        info = self._intel.read()

        self._process(info)

    def _listen(self):

        while True:
            self._advance()

    def listen(self):

        """
        Begin listening for events.
        """

        self._listen()