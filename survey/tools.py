import enum
import types
import wrapio
import os
import string
import itertools

from . import helpers


__all__ = ('Source', 'Translator', 'LineEditor', 'MultiLineEditor', 'Select',
           'MultiSelect')


_blocks = string.whitespace + string.punctuation


class Source(helpers.Handle):

    """
    Turns stdin reads into events.
    """

    Event = enum.Enum(
        'Event',
        'move_left move_right jump_left jump_right move_up move_down '
        'delete_left delete_right escape indent enter insert'
    )

    _events = types.SimpleNamespace(
        arrows = {
            'D': Event.move_left,
            'C': Event.move_right,
            'A': Event.move_up,
            'B': Event.move_down
        },
        normal = {
            '\x0d': Event.enter,
            '\x0a': Event.enter,
            '\x7f': Event.delete_left,
            '\x08': Event.delete_right,
            '\x09': Event.indent
        },
        special = {
            '': Event.escape,
            'b': Event.jump_left,
            'f': Event.jump_right
        }
    )

    __slots__ = ('_io', '_done')

    def __init__(self, io, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._io = io

        self._done = False

    def _escape(self):

        key = self._io.recv()

        if key == '[':
            key = self._io.recv()
            events = self._events.arrows
        else:
            events = self._events.special

        return (events, key)

    def _advance(self):

        key = self._io.recv()

        if key == '\x1b':
            (events, key) = self._escape()
        else:
            events = self._events.normal

        event = events.get(key, self.Event.insert)

        self._dispatch(event, key)

    def done(self):

        self._done = True

    def stream(self):

        with self._io.atomic:
            while not self._done:
                self._advance()

        self._done = False


class Abort(Exception):

    """
    Raise when something's wrong.
    """

    __slots__ = ()


class Translator(helpers.Handle):

    """
    Combines related io events into single events with relevant info.

    .. code-block: python

        translator = Translator(callback = ...)
        source = Source(io, callback = translator.invoke)
    """

    Event = enum.Enum(
        'Event',
        'move_x jump_x move_y delete insert enter'
    )

    __slots__ = ('_io',)

    def __init__(self, io, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._io = io

    def _move_x(self, left):

        self._dispatch(self.Event.move_x, left)

    @wrapio.event(Source.Event.move_left)
    def _nnc(self, key):

        self._move_x(True)

    @wrapio.event(Source.Event.move_right)
    def _nnc(self, key):

        self._move_x(False)

    def _jump_x(self, left):

        self._dispatch(self.Event.jump_x, left)

    @wrapio.event(Source.Event.jump_left)
    def _nnc(self, key):

        self._jump_x(True)

    @wrapio.event(Source.Event.jump_right)
    def _nnc(self, key):

        self._jump_x(False)

    def _move_y(self, up):

        self._dispatch(self.Event.move_y, up)

    @wrapio.event(Source.Event.move_up)
    def _nnc(self, key):

        self._move_y(True)

    @wrapio.event(Source.Event.move_down)
    def _nnc(self, key):

        self._move_y(False)

    def _delete(self, left):

        self._dispatch(self.Event.delete, left)

    @wrapio.event(Source.Event.delete_left)
    def _nnc(self, key):

        self._delete(True)

    @wrapio.event(Source.Event.delete_right)
    def _nnc(self, key):

        self._delete(False)

    def _insert(self, key):

        self._dispatch(self.Event.insert, key)

    @wrapio.event(Source.Event.insert)
    def _nnc(self, key):

        self._insert(key)

    @wrapio.event(Source.Event.indent)
    def _nnc(self, key):

        self._insert('\t')

    def _enter(self, key):

        self._dispatch(self.Event.enter, key)

    @wrapio.event(Source.Event.enter)
    def _nnc(self, key):

        self._enter(key)

    def invoke(self, *args, **kwargs):

        try:
            fail = super().invoke(*args, **kwargs)
        except Abort:
            fail = True
        else:
            if fail:
                return
            fail = False

        if fail:
            self._io.ring()

        return fail


class WindowView:

    """
    ABC for classes implementing something that can be partially viewed.
    """

    __slots__ = () # ('_index', '_lower', '_bound') on each subclass

    def __init__(self, bound):

        self._index = 0
        self._lower = 0
        self._bound = bound

    @property
    def _upper(self):

        return self._lower + self._bound

    @property
    def _among(self):

        return self._index - self._lower

    @property
    def among(self):

        return self._among

    @property
    def index(self):

        return self._index

    def _calibrate(self):

        if self._index < self._lower:
            # |[abc] <- [|ab]c
            self._lower = self._index
        elif self._index > self._upper:
            # [abc]| -> a[bc|]
            self._lower = self._index - self._bound
        else:
            return False

        return True

    def _resize(self, size):

        bound = self._bound + size

        if bound < 0:
            raise ValueError('bound would be negative')

        self._bound += size

        if size > 0:
            self._lower = max(0, self._lower - size)

        self._calibrate()

    def _reset(self):

        self._index = 0
        self._lower = 0


class Tool(WindowView, helpers.Handle):

    """
    ABC for partially-viewable handlers.
    """

    __slots__ = ('_index', '_lower', '_bound', '_io', '_cursor')

    def __init__(self, io, cursor, bound, *args, **kwargs):

        WindowView.__init__(self, bound)
        helpers.Handle.__init__(self, *args, **kwargs)

        self._io = io
        self._cursor = cursor

    def _clear(self):

        raise NotImplementedError()

    def clear(self):

        self._clear()

    def _draw(self, lower):

        raise NotImplementedError()

    def draw(self):

        self._draw(self._lower)

    def _focus(self):

        raise NotImplementedError()

    def focus(self):

        self._focus()

    def _redraw(self, skip = False):

        if not skip:
            self._clear()

        self._draw(self._lower)

        self._focus()

    def resize(self, size, full = True):

        if full:
            self._clear()

        self._resize(size)

        if full:
            self._redraw(skip = True)

    def _move_y(self, up, size):

        pass

    def _e_move_y(self, up, size):

        self._move_y(up, size)

        self._dispatch('move_y', up, size)

    @wrapio.event(Translator.Event.move_y)
    def _nnc(self, up):

        self._e_move_y(up, 1)

    def _move_x(self, left, size):

        pass

    def _e_move_x(self, left, size):

        self._move_x(left, size)

        self._dispatch('move_x', left, size)

    @wrapio.event(Translator.Event.move_x)
    def _nnc(self, left):

        self._e_move_x(left, 1)

    def _jump_x(self, left):

        pass

    def _e_jump_x(self, left):

        self._jump_x(left)

        self._dispatch('jump_x', left)

    @wrapio.event(Translator.Event.jump_x)
    def _nnc(self, left):

        self._e_jump_x(left)

    def _tab(self):

        pass

    def _e_tab(self):

        self._tab()

        self._dispatch('tab')

    def _insert(self, runes):

        pass

    def _e_insert(self, runes):

        if '\t' in runes:
            self._e_tab()
            return

        runes = self._insert(runes)

        self._dispatch('insert', runes)

        return runes

    def insert(self, runes):

        runes = self._e_insert(runes)

        return runes

    @wrapio.event(Translator.Event.insert)
    def _nnc(self, rune):

        runes = (rune,)

        self._e_insert(runes)

    def _delete(self, left, size):

        pass

    def _e_delete(self, left, size):

        self._delete(left, size)

        self._dispatch('delete', left, size)

    def delete(self, left, size):

        self._e_delete(left, size)

    @wrapio.event(Translator.Event.delete)
    def _nnc(self, left):

        self._e_delete(left, 1)

    def _submit(self):

        self._dispatch('submit')

    def _enter(self):

        raise NotImplementedError()

    @wrapio.event(Translator.Event.enter)
    def _nnc(self, rune):

        self._enter()


def _clean(value):

    value = helpers.seq.clean(value)
    value = helpers.clean(value)

    return value


class LineEditor(Tool):

    """
    Use for editing a single line of text.

    Does not support line breaks or moving vertically.
    """

    __slots__ = ('_limit', '_funnel', '_buffer')

    def __init__(self,
                 io,
                 cursor,
                 width,
                 limit,
                 funnel,
                 *args,
                 **kwargs):

        super().__init__(io, cursor, width, **kwargs)

        self._limit = limit

        self._funnel = funnel

        self._buffer = []

    @property
    def buffer(self):

        return self._buffer

    def _place(self):

        self._cursor.left(self._among)

    def _clear(self):

        self._place()

        self._cursor.erase()

    def _transform(self, rune):

        rune = self._funnel(rune)

        if not len(rune) == 1:
            raise RuntimeError('rune must be of size 1')

        if not rune.isprintable():
            raise RuntimeError('rune must be printable')

        return rune

    def _show(self, runes):

        if self._funnel:
            runes = map(self._transform, runes)

        runes = tuple(runes)

        value = ''.join(runes)

        self._io.send(value)

    def _chunk(self, lower):

        runes = self._buffer[lower:self._upper]

        return runes

    def _draw(self, lower):

        runes = self._chunk(lower)

        self._show(runes)

    @property
    def _shown(self):

        return len(self._chunk(self._lower))

    def _focus(self):

        size = self._shown - self._among

        self._cursor.left(size)

    def _move_x(self, left, size):

        if left:
            limit = self._index
        else:
            limit = len(self._buffer) - self._index

        excess = size - limit
        if excess > 0:
            raise Abort(excess)

        if left:
            index = self._index - size
            limit = self._among
            self._cursor.left(min(limit, size))
        else:
            index = self._index + size
            limit = self._shown - self._among
            self._cursor.right(min(limit, size))

        self._index = index

        change = self._calibrate()

        if change:
            self._redraw()

        return change

    def move(self, left, size):

        self._move_x(left, size)

    def _jump_x_left(self):

        limit = 0

        stop = self._index - 1

        if stop < limit:
            raise Abort()

        indexes = []
        for block in _blocks:
            try:
                index = helpers.rindex(self._buffer, block, 0, stop)
            except ValueError:
                continue
            indexes.append(index + 1)
        else:
            indexes.append(limit)

        size = min(self._index - index for index in indexes)

        self._move_x(True, size)

    def _jump_x_right(self):

        limit = len(self._buffer)

        start = self._index + 1

        if start > limit:
            raise Abort()

        indexes = []
        for block in _blocks:
            try:
                index = self._buffer.index(block, start)
            except ValueError:
                continue
            indexes.append(index)
        else:
            indexes.append(limit)

        size = min(index - self._index for index in indexes)

        self._move_x(False, size)

    def _jump_x(self, left):

        if left:
            self._jump_x_left()
        else:
            self._jump_x_right()

    def jump(self, left):

        self._jump_x(left)

    def _ensure(self, runes):

        value = ''.join(runes)
        value = _clean(value)

        return value

    def _insert(self, runes):

        runes = self._ensure(runes)
        runes = tuple(runes)

        esize = len(runes)
        osize = len(self._buffer)
        nsize = osize + esize

        if not self._limit is None and nsize > self._limit:
            raise Abort()

        start = self._index

        for (index, rune) in enumerate(runes):
            self._buffer.insert(start + index, rune)

        among = not start == osize

        self._index = start + esize

        change = self._calibrate()

        if change:
            self._redraw()
        elif among:
            self._draw(start)
            self._focus()
        else:
            self._show(runes)

        return runes

    def _delete(self, left, size):

        if left:
            self._move_x(True, size)

        limit = len(self._buffer) - self._index

        excess = size - limit
        if excess > 0:
            raise Abort(excess)

        for _ in range(size):
            del self._buffer[self._index]

        self._cursor.erase()

        self._draw(self._index)

        self._focus()

    def _enter(self):

        self._submit()


class Originful:

    __slots__ = () # ('_origin',) on each subclass

    def _originate(self):

        (cy, cx) = self._cursor.locate()

        self._origin = cx - 1


class MultiLineEditor(Tool, Originful):

    """
    Use for editing multiple lines of text.

    Supports line breaks or moving vertically.
    """

    __slots__ = ('_origin', '_finchk', '_subs', '_make', '_limit', '_indent')

    def __init__(self,
                 io,
                 cursor,
                 finchk,
                 height,
                 width,
                 limit,
                 funnel,
                 indent,
                 *args,
                 **kwargs):

        Tool.__init__(self, io, cursor, height - 1, *args, **kwargs)

        self._finchk = finchk

        make = lambda: LineEditor(io, cursor, width, None, funnel)

        self._subs = [make()]

        self._make = make

        self._limit = limit

        self._indent = indent

        self._originate()

    @property
    def _sub(self):

        return self._subs[self._index]

    @property
    def subs(self):

        return self._subs

    def _place(self):

        self._cursor.last(self._among)
        self._cursor.right(self._origin)

    def _clear(self):

        self._place()

        self._cursor.clear()

    def _chunk(self, lower):

        upper = self._upper + 1

        runes = self._subs[lower:upper]

        return runes

    def _draw(self, lower):

        self._originate()

        subs = self._chunk(lower)

        last = len(subs) - 1
        for (index, sub) in enumerate(subs):
            sub.draw()
            if index == last:
                break
            self._io.send(os.linesep)

    @property
    def _shown(self):

        return len(self._chunk(self._lower))

    def _focus(self):

        # if 1 shown and among 0, then move 0
        ysize = self._shown - self._among - 1

        self._cursor.last(ysize)

        xsize = self._sub.among

        if not self._among:
            xsize += self._origin

        self._cursor.right(xsize)

    _SpotType = enum.Enum('SpotType', 'match left right')

    def _spot(self, old, new, type):

        to_left = - new.index
        to_right = len(new.buffer) + to_left

        if type is self._SpotType.match:
            difference = old.index - new.index
            size = max(to_left, min(to_right, difference))
        elif type is self._SpotType.left:
            size = to_left
        elif type is self._SpotType.right:
            size = to_right
        else:
            raise ValueError('unknown move type')

        new.move(size < 0, abs(size))

    def _move_y(self, up, size, type = _SpotType.match):

        if up:
            limit = self._index
        else:
            # if 1 sub and index 0, then limit is 0
            limit = len(self._subs) - self._index - 1

        excess = size - limit
        if excess > 0:
            raise Abort(excess)

        if up:
            index = self._index - size
            limit = self._among
            self._cursor.last(min(limit, size))
        else:
            index = self._index + size
            limit = self._shown - self._among - 1
            self._cursor.next(min(limit, size))

        old = self._sub
        self._index = index
        new = self._sub

        xsize = new.among
        if not self._among:
            xsize += self._origin
        self._cursor.right(xsize)

        change = self._calibrate()

        if change:
            self._redraw()

        if not type is None:
            self._spot(old, new, type)

    def _rcut(self, left):

        if left:
            (*subs, sub) = self._subs[:self._index + 1]
            buffer = sub.buffer[:sub.index]
            subs = reversed(subs)
        else:
            (sub, *subs) = self._subs[self._index:]
            buffer = sub.buffer[sub.index:]

        buffers = (buffer, *(sub.buffer for sub in subs))

        return buffers

    def _rmsr(self, buffers, xsize):

        ysize = 0
        nsize = xsize
        for buffer in buffers:
            nsize -= len(buffer) + 1
            if nsize < 0:
                break
            xsize = nsize
            ysize += 1

        return (ysize, xsize)

    def _rclc(self, left, xsize):

        buffers = self._rcut(left)

        # remove one to account for current line
        limit = sum(map(len, buffers)) + len(buffers) - 1

        excess = xsize - limit
        if excess > 0:
            raise Abort(excess)

        (ysize, xsize) = self._rmsr(buffers, xsize)

        return (ysize, xsize)

    def _move_x(self, left, xsize):

        (ysize, xsize) = self._rclc(left, xsize)

        if ysize:
            type = self._SpotType.right if left else self._SpotType.left
            self._move_y(left, ysize, type)

        self._sub.move(left, xsize)

        return (ysize, xsize)

    def move(self, left, size):

        self._move_x(left, size)

    def _jump_x(self, left):

        try:
            self._sub.jump(left)
        except Abort:
            self._move_x(left, 1)

    def _ensure(self, runes):

        esize = len(runes)
        buffers = tuple(sub.buffer for sub in self._subs)
        osize = sum(map(len, buffers)) + len(buffers) - 1
        nsize = osize + esize

        if not self._limit is None and nsize > self._limit:
            raise Abort()

    def _tab(self):

        self._e_insert((' ',) * self._indent)

    def _insert(self, runes):

        values = helpers.split(runes, os.linesep)
        values = tuple(values)

        runes = tuple(itertools.chain.from_iterable(values))

        self._ensure(runes)

        last = len(values) - 1
        buffer = []
        for (index, runes) in enumerate(values):
            runes = self._sub.insert(runes)
            buffer.extend(runes)
            if index == last:
                break
            self._newsub()
            buffer.append(os.linesep)

        return buffer

    def _delete(self, left, size):

        if left:
            self._move_x(True, size)

        (ysize, xsize) = self._rclc(False, size)

        kli = self._index + 1
        sub = self._sub

        for index in range(ysize):
            nsub = self._subs.pop(kli)
            sub.buffer.extend(nsub.buffer)

        if ysize:
            self._redraw()

        sub.delete(False, size - ysize)

    def _newsub(self):

        old = self._sub

        new = self._make()

        while True:
            try:
                rune = old.buffer.pop(old.index)
            except IndexError:
                break
            new.buffer.append(rune)

        last = self._index == len(self._subs) - 1 and self._among < self._bound
        full = not last

        if full:
            self._clear()
        else:
            self._cursor.erase()

        index = self._index + 1

        self._subs.insert(index, new)

        self._index = index

        runes = (os.linesep,)

        if full:
            self._calibrate()
            self._redraw(skip = True)
        else:
            self._io.send(*runes)
            self._draw(self._index)
            self._focus()

        self._dispatch('insert', runes)

    def newsub(self):

        self._newsub()

    def _enter(self):

        done = self._finchk()

        (self._submit if done else self._newsub)()


class Select(Tool, Originful):

    """
    Use for cycling through and selecting options.
    """

    __slots__ = ('_origin', '_options', '_visible', '_changed', '_buffer',
                 '_width', '_prefix', '_indent', '_funnel', '_filter')

    def __init__(self,
                 io,
                 cursor,
                 height,
                 width,
                 options,
                 prefix,
                 indent,
                 funnel,
                 filter,
                 *args,
                 **kwargs):

        Tool.__init__(self, io, cursor, height - 1, *args, **kwargs)

        self._options = options
        self._visible = tuple(range(len(options)))
        self._changed = {}

        self._buffer = []

        self._width = width

        self._prefix = prefix
        self._indent = indent

        self._funnel = funnel
        self._filter = filter

        self._originate()

    @property
    def buffer(self):

        return self._buffer

    def _place(self):

        self._cursor.last(self._among)
        self._cursor.right(self._origin)

    def _clear(self):

        self._place()

        self._cursor.clear()

    def _tran(self, index, current, option):

        return option

    def _chunk(self, lower):

        return self._visible[lower:self._upper + 1]

    def _fetch(self, index, current):

        option = self._options[index][:self._width]

        if current:
            try:
                option = self._changed[index]
            except KeyError:
                if self._funnel:
                    option = self._funnel(index, option)
                self._changed[index] = option

        prefix = self._prefix if current else ' ' * self._indent

        option = prefix + self._tran(index, current, option)

        return option

    def _show(self, index, current):

        self._cursor.erase()

        option = self._fetch(index, current)

        self._io.send(option)

        self._cursor.goto(0)

    def _draw(self, lower):

        indexes = self._chunk(lower)

        options = []
        for (cindex, oindex) in enumerate(indexes, start = lower):
            current = cindex == self._index
            option = self._fetch(oindex, current)
            options.append(option)

        result = os.linesep.join(options)

        self._io.send(result)

    @property
    def _shown(self):

        return len(self._chunk(self._lower))

    def _focus(self):

        # if 1 shown and among 0, then move 0
        ysize = self._shown - self._among - 1

        self._cursor.last(ysize)

        xsize = 0 # doesn't matter

        if not self._among:
            xsize += self._origin

        self._cursor.right(xsize)

    def _slide(self, up, size):

        limit = len(self._visible)

        size = size % limit

        index = self._index + (- size if up else size)

        if index < 0:
            index = limit - 1
        else:
            extra = index - limit
            if not extra < 0:
                index = extra

        size = index - self._index

        up = size < 0
        size = abs(size)

        return (up, size, index)

    def _move_y(self, up, size):

        (up, size, index) = self._slide(up, size)

        if up:
            limit = self._index
        else:
            # if 1 sub and index 0, then limit is 0
            limit = len(self._visible) - self._index - 1

        # no need to check excess, ``_slide`` ensures

        self._show(self._visible[self._index], False)

        if up:
            limit = self._among
            self._cursor.last(min(limit, size))
        else:
            limit = self._shown - self._among - 1
            self._cursor.next(min(limit, size))

        self._index = index

        change = self._calibrate()

        if change:
            self._redraw()
        else:
            self._show(self._visible[index], True)

    def move(self, up, size):

        self._move_y(up, size)

    def _specify(self, new):

        argument = ''.join(self._buffer)

        if new:
            indexes = self._visible
            options = (self._options[index] for index in indexes)
            pairs = zip(indexes, options)
            pairs = self._filter(pairs, argument)
            (indexes, options) = zip(*pairs)
        else:
            indexes = range(len(self._options))

        self._clear()

        self._visible = indexes

        self._index = 0

        self._calibrate()

        self._redraw(skip = True)

        self._dispatch('filter', argument)

    def _insert(self, runes):

        save = self._buffer.copy()

        value = ''.join(runes)
        value = _clean(value)

        self._buffer.extend(value)

        try:
            self._specify(True)
        except ValueError:
            self._buffer.clear()
            self._buffer.extend(save)
            raise Abort()

    def _delete(self, left, size):

        if not self._buffer:
            raise Abort()

        self._buffer.clear()

        self._specify(False)

    def _enter(self):

        self._submit()


class MultiSelect(Select):

    __slots__ = ('_unpin', '_pin', '_chosen')

    def __init__(self, unpin, pin, indexes, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._unpin = unpin
        self._pin = pin

        self._chosen = set(indexes)

    @property
    def indexes(self):

        return self._chosen

    def _tran(self, index, current, option):

        signal = self._pin if index in self._chosen else self._unpin

        return signal + super()._tran(index, current, option)

    def _add(self, index, full):

        if full:
            limit = len(self._options)
            if len(self._chosen) == limit:
                raise Abort()
            self._chosen.update(range(limit))
        else:
            self._chosen.add(index)

    def _pop(self, index, full):

        if full:
            if not self._chosen:
                raise Abort()
            self._chosen.clear()
        else:
            self._chosen.remove(index)

    def _inform(self, new):

        index = self._visible[self._index]

        exists = index in self._chosen
        full = exists if new else not exists

        (self._add if new else self._pop)(index, full)

        self._redraw()

        self._dispatch('inform', new, full)

    def _move_x(self, left, size):

        new = not left

        self._inform(new)
