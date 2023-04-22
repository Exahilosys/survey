
"""
Classes for printing data that can change over time.
"""

import typing
import abc
import functools
import time
import math
import threading
import collections

from . import _core
from . import _helpers
from . import _system
from . import _colors
from . import _theme


__all__ = ('Graphic', 'BaseProgress', 'SpinProgress', 'LineProgress')


class Graphic(abc.ABC):

    """
    Base for graphics.

    :param inline:
        Whether ``\\n`` should **not** be used upon closing.
    :param frequency:
        Seconds for printing time throttling.
    :param epilogue:
        Shown upon closing instead of the completed graphic.
    """

    _lock = threading.RLock()

    _top_point = (0, 0)
    _cur_count = 0

    def __init__(self, 
                 inline   : bool = False, 
                 frequency: float = 0.1,
                 epilogue : str | typing.Callable[[], str] | None = None):

        self._inline = inline

        self._frequency = frequency
        self._time_last = 0

        self._epilogue = epilogue

        io = _system.io
        cursor = _system.cursor
        render = _core.Render(cursor, io)
        screen = _core.Screen(render, cursor)

        self._io = io
        self._cursor = cursor
        self._render = render
        self._screen = screen

        self._cur_index = None
        self._cur_point = None

    @abc.abstractmethod
    def _get(self):

        return NotImplemented
    
    @property
    def _final(self):

        return self._cur_point == self._top_point

    def _sketch(self, close):

        if close and not (value := self._epilogue) is None:
            if callable(value):
                value = value()
        else:
            value = self._get()

        lines = _helpers.split_lines(value)
        point = None

        return (lines, point)
    
    @_helpers.ctxmethod(lambda self: self._lock)
    def _print(self, check, *, close = False):

        time_next = time.time()

        if check and time_next - self._time_last < self._frequency:
            return
        
        self._time_last = time_next

        sketch = functools.partial(self._sketch, close)

        self._screen.print(sketch, True, clean = False)

        if not close:
            self._cur_point = point = self._cursor.locate()
            self.__class__._top_point = max(self._top_point, point)

    @_helpers.ctxmethod(lambda self: self._lock)
    def _start(self):

        if not self._cur_index is None:
            return

        self._cur_index = self._cur_count

        self.__class__._cur_count += 1

        if self._cur_index:
            self._render.draw([[], []], learn = False, clean = False)

        self._print(False)

    def start(self):

        """
        Start the graphic. Calling this is required before further use.
        """

        self._start()

    @_helpers.ctxmethod(lambda self: self._lock)
    def _close(self):

        self._print(False, close = True)

        self.__class__._cur_count -= 1

        if self._cur_count:
            return
        
        if not self._final:
            self._cursor.move(*self._top_point)

        if not self._inline:
            sketch = lambda: ([[], []], None)
            self._screen.print(sketch, False, learn = False)

    def close(self):

        """
        Close the graphic. Calling this is required after complete use.
        """

        self._close()
 
    def __enter__(self, *args):

        self._cursor.hidden.enter()

        self._start()

        return self

    def __exit__(self, *args):

        self._close()

        self._cursor.hidden.leave()


class BaseProgress(Graphic):

    """
    Base for progress graphics.
    """

    def __init__(self, *args, **kwargs):

        self._cycle_actual = 0
        self._cycle_memory = 0

        super().__init__(*args, **kwargs)

    def _print(self, check, *args, **kwargs):

        size = self._cycle_memory

        if check and not size > 0:
            return
        
        self._cycle_actual += size
        self._cycle_memory = 0

        super()._print(check, *args, **kwargs)

    def _set(self, step):

        self._cycle_memory = max(0, step)

        self._print(True)

    def set(self, step):

        """
        Set the progress to a specific step.
        """

        self._set(step)

    def _add(self, size):

        step = self._cycle_memory + size
        
        self._set(step)

    def add(self, size):

        """
        Add to the current progress step.
        """

        self._add(size)


class SpinProgress(BaseProgress):

    """
    Progress "spinner" with undeterminable ending condition.

    :param phases:
        The phases to cycle over when adding ``1`` progress.
    :param prefix:
        Prepended to the phase.
    :param suffix:
        Appended to the phase.
    
    .. code-block:: python

        with survey.graphics.SpinProgress(prefix = 'Loading ', epilogue = 'Done!') as progress:
            for _ in range(10):
                progress.add(1)
                time.sleep(.35)

    |theme| :code:`graphics.SpinProgress`.

    .. image:: /_static/images/graphics.spinprogress-1.gif
    """

    @_theme.add('graphics.SpinProgress')
    def __init__(self, 
                 *args,
                 phases: list[str] = ('.', 'o', 'O', '@', '*'),
                 prefix: str       = ' ',
                 suffix: str       = '',
                 **kwargs):

        self._prefix = prefix
        self._suffix = suffix

        self._phases = phases

        super().__init__(*args, **kwargs)

    def _get(self):

        cycle = self._cycle_actual % len(self._phases)

        value = (
              self._prefix
            + self._phases[cycle] 
            + self._suffix
        )

        return value
    

class LineProgress(BaseProgress):

    """
    Progress line with a clear start and end.

    :param total:
        The maximum progress value.
    :param width:
        The length of the line.
    :param phases:
        The fractional phases possible. The last one is used for a full bar. 
        Multiple full bars and at most 1 fractional make up the whole line.
    :param empty:
        Used for filling in the empty space.
    :param prefix_wall:
        Prepended to the line.
    :param suffix_wall:
        Appended to the line.
    :param prefix:
        Prepended to the final value.
    :param suffix:
        Appended to the final value.
    :param percentage_zfill_value:
        Used for padding the percentage.
    :param percentage_zfill_color:
        Used for painting the percentage padding.
    :param percentage_zfill_count:
        The maximum amount of percentage padding.
    :param throughput_zfill_value:
        Used for padding the throughput.
    :param throughput_zfill_color:
        Used for painting the throughput padding.
    :param throughput_zfill_count:
        The maximum amount of throughput padding.

    The final structure is as follows:

    .. code-block::

        (prefix)(percentage + ' ')(prefix_wall)(phases[-1]*?)(phases[?])(empty*?)(suffix_wall)(' ' + throughput)(suffix)

    .. code-block:: python

        with survey.graphics.LineProgress(100, prefix = 'Loading ') as progress:
            for _ in range(100):
                progress.add(1)
                time.sleep(0.035)

    |theme| :code:`graphics.LineProgress`.

    .. image:: /_static/images/graphics.lineprogress-1.gif
    """

    @_theme.add('graphics.LineProgress')
    def __init__(self, 
                 total                 : int, 
                 *args,
                 width                 : int       = 50,
                 phases                : list[str] = ('-',), 
                 empty                 : str       = ' ',
                 prefix_wall           : str       = '[', 
                 suffix_wall           : str       = ']',
                 prefix                : str       = '',
                 suffix                : str       = '',
                 percentage_zfill_value: str       = '0',
                 percentage_zfill_color: str       = _colors.basic('black'),
                 percentage_zfill_count: str       = 3,
                 percentage_template   : str       = '{value}%',
                 throughput_zfill_value: str       = '0',
                 throughput_zfill_color: str       = _colors.basic('black'),
                 throughput_zfill_count: str       = 3,
                 throughput_template   : str       = '{value}/s',
                 **kwargs):

        self._prefix = prefix
        self._suffix = suffix

        self._total = total

        self._width = width

        self._empty = empty
        self._phases = phases
        self._prefix_wall = prefix_wall
        self._suffix_wall = suffix_wall

        self._percentage_template = percentage_template
        self._percentage_zfill_value = percentage_zfill_value
        self._percentage_zfill_color = percentage_zfill_color
        self._percentage_zfill_count = percentage_zfill_count
        
        self._throughput_template = throughput_template
        self._throughput_zfill_value = throughput_zfill_value
        self._throughput_zfill_color = throughput_zfill_color
        self._throughput_zfill_count = throughput_zfill_count
        self._throughput_deque = collections.deque(maxlen = 10)

        self._width = width

        super().__init__(*args, **kwargs)

    def _set(self, step):

        self._throughput_deque.append((time.time(), step))

        super()._set(step)

    def _get(self):

        size_limit = self._cursor.measure()[1]
        size_limit -= self._cursor.locate()[1]
        
        if not (size_given := self._width) is None:
            size_limit = min(size_given, size_limit)

        size_ratio = min(self._total, self._cycle_actual) / self._total

        percentage = ''
        if not (percentage_template := self._percentage_template) is None:
            percentage_value = str(math.ceil(size_ratio * 100))
            percentage_zfill_count = self._percentage_zfill_count - len(percentage_value)
            percentage_zfill_value = self._percentage_zfill_value * percentage_zfill_count
            if not (percentage_zfill_color := self._percentage_zfill_color) is None:
                percentage_zfill_value = _helpers.paint_text(percentage_zfill_color, percentage_zfill_value)
            percentage_value = percentage_zfill_value + percentage_value
            percentage = percentage_template.format(value = percentage_value)
            percentage = percentage + ' '

        full_size_limit = size_limit
        full_size_ratio = size_ratio
        full_size_precise = full_size_limit * full_size_ratio
        full_size = round(full_size_precise)

        half_size_limit = len(self._phases)
        half_size_ratio = full_size_precise - full_size
        half_size_precise = half_size_limit * half_size_ratio
        half_size = math.floor(half_size_precise)
        half_index = half_size % half_size_limit

        add_size = full_size_limit - full_size

        throughput = ''
        if not (throughput_template := self._throughput_template) is None:
            try:
                throughput_times, throughput_steps = zip(*self._throughput_deque)
                throughput_period = max(throughput_times) - min(throughput_times)
                throughput_amount = sum(throughput_steps)
                throughput_ratio = throughput_amount / throughput_period
            except (ValueError, ZeroDivisionError):
                throughput_value = ''
            else:
                throughput_value = str(math.ceil(throughput_ratio * 100))
            throughput_zfill_count = self._throughput_zfill_count - len(throughput_value)
            throughput_zfill_value = self._throughput_zfill_value * throughput_zfill_count
            if not (throughput_zfill_color := self._throughput_zfill_color) is None:
                throughput_zfill_value = _helpers.paint_text(throughput_zfill_color, throughput_zfill_value)
            throughput_value = throughput_zfill_value + throughput_value
            throughput = throughput_template.format(value = throughput_value)
            throughput = ' ' + throughput

        line = (
              self._prefix
            + percentage
            + self._prefix_wall 
            + self._phases[- 1] * full_size
            + self._phases[half_index] 
            + self._empty * add_size
            + self._suffix_wall
            + throughput
            + self._suffix
        )

        return line