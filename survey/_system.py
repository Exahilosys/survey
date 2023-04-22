
"""
Core assets used throughout the module that read and write to the system io buffers.
"""

import sys

from . import _core


__all__ = ('io', 'cursor', 'render', 'handle', 'screen', 'console')


#:
_io = io = _core.IO(sys.stdin, sys.stdout)

#:
_handle = handle = _core.Handle(_io)

#:
_cursor = cursor = _core.Cursor(_io)

#:
_render = render = _core.Render(_cursor, _io)

#:
_screen = screen = _core.Screen(_render, _cursor)

#:
_console = console = _core.Console(_handle, _screen)

