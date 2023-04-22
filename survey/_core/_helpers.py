import contextlib
import importlib
import os
import threading
import copy
import functools


def noop(*args, **kwargs):

    pass


@contextlib.contextmanager
def noop_contextmanager(*args, **kawrgs):

    yield


def import_module_os(name):

    name = '.' + name + '_os_' + os.name

    module = importlib.import_module(name, package = __package__)

    return module


def ctxmethod(get):

    def decorator(function):
        @functools.wraps(function)
        def wrapper(self, *args, **kwargs):
            with get(self):
                return function(self, *args, **kwargs)
        return wrapper
    
    return decorator


class Atomic:

    __slots__ = ('__enter', '__leave', '_size', '_lock')

    def __init__(self, enter = None, leave = None):

        self.__enter = enter
        self.__leave = leave

        self._size = 0
        self._lock = threading.Lock()

    @property
    def open(self):

        return not self._size

    @ctxmethod(lambda self: self._lock)
    def _deduce(self, function, step, limit):

        size = self._size + step

        if not size > limit and function:
            function()

        self._size = size

    def _enter(self):

        self._deduce(self.__enter, 1, 1)

    def enter(self):

        self._enter()

    def _leave(self):

        self._deduce(self.__leave, - 1, 0)

    def leave(self):

        self._leave()

    def __enter__(self):

        self._enter()

    def __exit__(self, type, value, traceback):

        self._leave()
