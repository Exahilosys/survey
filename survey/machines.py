import os

from . import tools


__all__ = ()


class Machine:

    __slots__ = ()

    def get(self):

        raise NotImplementedError()

    def view(self, value):

        raise NotImplementedError()


class LineEditor(tools.LineEditor, Machine):

    __slots__ = ()

    def get(self):

        result = ''.join(self._buffer)

        return result

    def view(self, value):

        result = (value,)

        return result


class MultiLineEditor(tools.MultiLineEditor, Machine):

    __slots__ = ()

    def get(self):

        subget = lambda sub: LineEditor.get(sub)

        result = os.linesep.join(map(subget, self._subs))

        return result

    def view(self, value):

        result = (value,)

        return result


class Select(tools.Select, Machine):

    __slots__ = ()

    def get(self):

        result = self._visible[self._index]

        return result

    def view(self, index):

        option = self._options[index]

        result = (option,)

        return result


class MultiSelect(tools.MultiSelect, Machine):

    __slots__ = ()

    def get(self):

        result = self._chosen

        return result

    def view(self, indexes):

        indexes = sorted(indexes)

        result = tuple(self._options[index] for index in indexes)

        return result
