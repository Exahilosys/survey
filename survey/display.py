import os
import collections
import itertools

from . import helpers


__all__ = ('Display',)


class Graphic:

    _Visual = collections.namedtuple('Visual', 'dirty ready clean')

    __slots__ = ('_io', '_cursor', '_visuals', '_origin', '_width')

    def __init__(self, io, cursor):

        self._io = io
        self._cursor = cursor

        self._visuals = []
        self._origin = None

        self._width = None

    @property
    def visuals(self):

        return self._visuals

    def reset(self):

        self._visuals.clear()

    def resize(self, width):

        self._width = width

    def _locate(self):

        (cy, cx) = self._cursor.locate()

        self._origin = cx - 1

    def locate(self):

        self._locate()

    def _originate(self, index):

        if index < 0:
            return self._origin

        visual = self._visuals[index]

        lines = visual.clean.rsplit(os.linesep, 1)
        origin = len(lines.pop()) # removes last

        if not lines: # checks if empty
            origin += self._originate(index - 1)

        return origin

    def _draw(self, index):

        visuals = self._visuals[index:]

        for visual in visuals:
            self._io.send(visual.ready)

    def _clear(self, index):

        visuals = self._visuals[index:]

        ysize = 0
        for visual in visuals:
            ysize += visual.clean.count(os.linesep)

        self._cursor.last(ysize)

        xsize = self._originate(index - 1)

        self._cursor.right(xsize)

        self._cursor.clear()

    @staticmethod
    def _clean(value):

        value = helpers.seq.clean(value)
        runes = helpers.clean(value, ignore = {os.linesep})
        value = ''.join(runes)

        return value

    def _format(self, index, value):

        clean = self._clean(value)
        lines = clean.split(os.linesep)

        current = self._originate(index - 1)

        # injects \n whenever part of each
        # line is about to exceed the width
        step = self._width
        for (state, line) in enumerate(lines):
            index = step
            if not state:
                index -= current
            for cycle in itertools.count():
                if not index < len(line):
                    break
                value = helpers.seq.inject(value, index + cycle, os.linesep)
                index += step

        return value

    def _build(self, index, dirty):

        ready = self._format(index, dirty)
        clean = self._clean(ready)

        visual = self._Visual(dirty, ready, clean)

        return visual

    def _insert(self, index, value):

        visual = self._build(index, value)

        self._visuals.insert(index, visual)

        after = index + 1
        values = []
        while True:
            try:
                visual = self._visuals.pop(after)
            except IndexError:
                break
            values.append(visual.dirty)

        for (subindex, value) in enumerate(values, start = after):
            visual = self._build(subindex, value)
            self._visuals.insert(subindex, visual)

        self._draw(index)

        return visual

    def _create(self, index, value):

        visual = self._insert(index, value)

        return visual

    def create(self, value, index = None):

        if index is None:
            index = len(self._visuals)

        return self._create(index, value)

    def _remove(self, index):

        self._clear(index)

        visual = self._visuals.pop(index)

        return visual

    def _delete(self, index):

        visual = self._remove(index)

        self._draw(index)

        return visual

    def delete(self, index):

        return self._delete(index)

    def _update(self, index, value):

        self._remove(index)

        visual = self._insert(index, value)

        return visual

    def update(self, index, value):

        return self._update(index, value)


class Display:

    __slots__ = ('_graphic',)

    def __init__(self, io, cursor):

        self._graphic = Graphic(io, cursor)

    @property
    def _size(self):

        return len(self._graphic.visuals)

    def locate(self, width):

        self._graphic.locate()

        self._graphic.resize(width)

    def create(self, value, *rest, fall = 0):

        values = [value, *rest, fall * os.linesep]

        for value in values:
            if value is None:
                value = ''
            self._graphic.create(value)

    def update(self, *values):

        if len(values) > self._size - 1:
            raise ValueError('too many values')

        pairs = tuple(enumerate(values, start = 1))

        for (index, value) in reversed(pairs):
            if value is None:
                continue
            self._graphic.update(index, value)

    def finish(self, value, full = False):

        enter = not full
        leave = self._size
        indexes = range(enter, leave)
        for index in reversed(indexes):
            self._graphic.delete(index)

        if not value is None:
            self._graphic.create(value)

        self._graphic.reset()
