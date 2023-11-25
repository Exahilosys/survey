
"""
Classes for printing data that can change over time.
"""

import typing
import time
import math
import threading
import functools
import collections
import collections.abc
import copy

from . import _core
from . import _helpers
from . import _system
from . import _visuals
from . import _funnels
from . import _colors
from . import _theme


__all__ = ('SpinProgress', 'MultiLineProgress', 'MultiLineProgressControl',
           'LineProgress')


_type_init_Interface_frequency = float


class Interface:
    
    """
    The graphics manager, responsible for printing asynchronously.

    :param frequency:
        The "refresh rate" for all graphics.
        
    .. code-block:: python
    
        with Interface() as interface:
            interface.tiles.append(...)
    """

    __slots__ = ('_frequency', '_io', '_cursor', '_render', '_screen', 
                 '_visual_tiles', '_visual_point', '_visual', '_active', 
                 '_thread')

    @_theme.add('graphics.Interface')
    def __init__(self, 
                 frequency: _type_init_Interface_frequency):
        
        self._frequency = frequency

        io = _system.io
        cursor = _system.cursor
        render = _core.Render(cursor, io)
        screen = _core.Screen(render, cursor)

        self._io = io
        self._cursor = cursor
        self._render = render
        self._screen = screen

        visual_funnel_enter_group = []
        visual_funnel_enter_entry = _funnels.line_delimit('\n')
        visual_funnel_enter_group.append(visual_funnel_enter_entry)
        visual_funnel_enter = _helpers.chain_functions(*visual_funnel_enter_group)

        visual_tiles = []
        visual_point = [0, 0]
        visual = _visuals.Line.link(visual_tiles, visual_point, funnel_enter = visual_funnel_enter)

        self._visual_tiles = visual_tiles
        self._visual_point = visual_point
        self._visual = visual

        self._active = True
        self._thread = None

    @property
    def tiles(self) -> list[_visuals.Visual]:
        
        """
        The managed graphics.
        
        Can be modified in any way at any time.
        """

        return self._visual_tiles
    
    def _sketch(self, fin):

        lines, point = self._visual.get()

        if fin:
            lines.append([])

        return (lines, None)

    def _print(self, fin = False):

        sketch = functools.partial(self._sketch, fin)

        self._screen.print(sketch, True)

    def _cycle(self):

        while self._active:
            self._print()
            time.sleep(self._frequency)

    def _start(self):

        self._cursor.hidden.enter()

        thread = threading.Thread(target = self._cycle, daemon = True)

        thread.start()

        self._thread = thread

    def start(self):

        self._start()

    def _close(self):

        self._active = False

        if self._thread is None:
            return
        
        self._thread.join()

        self._print(fin = True)

        self._cursor.hidden.leave()

    def close(self):

        self._close()
        
        
_type_init_Visual_get      = _visuals._type_Text_init_get
_type_init_Visual_epoligue = typing.Union[str, typing.Callable[['Visual'], str]]

        
class Visual(_visuals.Text):
    
    """
    A base class that communicates with an :class:`.Interface` upon creation and deletion.
    
    :param get:
        Same as :paramref:`.visuals.Text.get`.
    :param epilogue:
        Used for the final print before closing.
    """

    _interface = None
    _interface_frequency = NotImplemented

    __slots__ = ('_epilogue', '_phantasm')

    def __init__(self, 
                 get     : _type_init_Visual_get, 
                 *args, 
                 epilogue: _type_init_Visual_epoligue = None,
                 **kwargs):

        self._epilogue = epilogue
        self._phantasm = None

        sub_get = get

        def get(*args, **kwargs):
            lines = self._phantasm
            if lines is None:
                value = sub_get(*args, **kwargs)
                lines = _helpers.split_lines(value)
            else:
                lines = copy.deepcopy(lines)
            point = [0, 0]
            return (lines, point)
        
        super().__init__(get, *args, **kwargs)

    def _start(self):

        init = self._interface is None

        if init:
            interface = self.__class__._interface = Interface(self._interface_frequency)
        else:
            interface = self._interface

        interface.tiles.append(self.get)

        if init:
            interface.start()

    def _close(self):
        
        epilogue = _helpers.get_or_call(self._epilogue, self)

        self._phantasm = self._get()[0] if epilogue is None else _helpers.split_lines(epilogue)

        interface = self._interface

        if any(get.__self__._phantasm is None for get in self._interface.tiles):
            return
        
        self.__class__._interface = None

        interface.close()

    def __enter__(self, *args):

        self._start()

        return self

    def __exit__(self, *args):

        self._close()
        

_type_init_Graphic_get        = typing.Union[str, typing.Callable[['Visual'], str]]
_type_init_Graphic_prefix     = typing.Union[str, typing.Callable[['Visual'], str]]
_type_init_Graphic_suffix     = typing.Union[str, typing.Callable[['Visual'], str]]
_type_init_Graphic_mark       = str
_type_init_Graphic_mark_color = str


class Graphic(Visual):
    
    """
    A base class for graphics.
    
    :param get:
        Same as :paramref:`.Visual.get`, except it should return `str`.
    :param prefix:
        Added before the result of :paramref:`.get`.
    :param suffix:
        Added after the result of :paramref:`.get`.
    :param mark:
        Added before :paramref:`.prefix`.
    :param mark_color:
        The color to paint :paramref:`.mark` with.
    """

    __slots__ = ('_info',)

    def __init__(self,
                 get       : _type_init_Graphic_get,
                 *args,
                 prefix    : _type_init_Graphic_prefix     = None,
                 suffix    : _type_init_Graphic_suffix     = None,
                 mark      : _type_init_Graphic_mark       = '! ', 
                 mark_color: _type_init_Graphic_mark_color = _colors.basic('cyan'),
                 **kwargs):
        
        super_cls = self.__class__.__mro__[1]

        epilogue = _helpers.get_function_arg_safe(super_cls, 'epilogue', kwargs, pop = True)

        mark = _helpers.paint_text(mark_color, mark)

        def merge_parts(parts):
            if not mark is None:
                parts.insert(0, mark)
            return ''.join(parts)

        def epilogue(*args, __sub = epilogue, **kwargs):
            value = _helpers.get_or_call(__sub, *args, **kwargs)
            if value is None:
                return value
            parts = [value]
            return merge_parts(parts)

        if not callable(prefix):
            sub_prefix = prefix
            prefix = lambda *args: sub_prefix

        if not callable(suffix):
            sub_suffix = suffix
            suffix = lambda *args: sub_suffix

        sub_get = get
        def get(*args):
            value = sub_get(*args)
            parts = []
            value_prefix = prefix(self)
            value_suffix = suffix(self)
            if not value_prefix is None:
                parts.append(value_prefix)
            parts.append(value)
            if not value_suffix is None:
                parts.append(value_suffix)
            return merge_parts(parts)
        
        super().__init__(get, *args, epilogue = epilogue, **kwargs)


class SpinProgress(Graphic):
    
    """
    A spinner indicating work of undeterminable size.
    
    :param runes:
        The characters to cycle through on every print.

    .. code-block:: python

        state = None
        with survey.graphics.SpinProgress(prefix = 'Loading ', suffix = lambda self: state, epilogue = 'Done!') as progress:
            for state in (state, ' calculating...', ' molding...', ' redering...'):
                time.sleep(2)
    
    |theme| :code:`graphics.SpinProgress`.

    .. image:: /_static/images/graphics.spinprogress-1.gif
    """

    _interface_frequency = 0.2

    __slots__ = ('_stage',)

    @_theme.add('graphics.SpinProgress')
    def __init__(self,
                 *args,
                 runes: typing.List[str] = ('|', '/', '—', '\\'),
                 **kwargs):

        self._stage = 0

        def get(*args):
            index = self._stage % len(runes)
            rune = runes[index]
            self._stage += 1
            return rune
        
        super().__init__(get, *args, **kwargs)


_type_MultiLineProgressControl_init_total               = typing.Union[int, float]
_type_MultiLineProgressControl_init_runes               = list[str]
_type_MultiLineProgressControl_init_color               = typing.Union[str, None]
_type_MultiLineProgressControl_init_value               = typing.Union[int, float]
_type_MultiLineProgressControl_init_deque_limit_size    = typing.Union[int, None]
_type_MultiLineProgressControl_init_deque_limit_time    = typing.Union[int, None]
_type_MultiLineProgressControl_init_info_value_template = str
_type_MultiLineProgressControl_init_info_speed_template = str
_type_MultiLineProgressControl_init_info_chron_template = str
_type_MultiLineProgressControl_init_info_delimit        = str
_type_MultiLineProgressControl_init_info_color          = _type_MultiLineProgressControl_init_color
_type_MultiLineProgressControl_init_info_epilogue       = typing.Union[str, typing.Callable[['MultiLineProgressControl'], str]]
_type_MultiLineProgressControl_init_info_extra          = typing.Union[str, typing.Callable[['MultiLineProgressControl'], str]]
_type_MultiLineProgressControl_init_info_denominate     = typing.Union[typing.Callable[[_type_MultiLineProgressControl_init_value], tuple[float, str]], None]

_type_MultiLineProgressControl_move_size             = _type_MultiLineProgressControl_init_value

_type_MultiLineProgressControl_get_line_width        = int


class MultiLineProgressControl:
    
    """
    A line indicating the progress of work of a certain size.
    
    :param total:
        The maximum expected amount of the internal value.
    :param runes:
        The runes to cycle through for subdivisions of a character.
    :param color:
        The color of the line.
    :param value:
        The initial value.
    :param deque_limit_size:
        The maximum amount of information to hold in the deque.
    :param deque_limit_time:
        The maximum amount of time to preserve information in the deque for.
    :param info_value_template:
        The info template of the current and total value. 
        
        - ``value`` is the current value. 
        - ``total`` is :paramref:`.total`.
        - ``unit`` is from :paramref:`.denominate`.
    :param info_speed_template:
        The info template of the known move speed.
        
        - ``speed`` is the known moving rate of the value. 
        - ``unit`` is from :paramref:`.denominate`.
    :param info_chron_template:
        The info template of the elapsed time and known remaining..
        
        - ``remain`` is the known time left until completion. 
        - ``elapse`` is the time spent since the first move.
    :param info_delimit:
        The text used to join all ``info_`` parts.
    :param info_epilogue:
        Used after the value has reached the total instead of the constructed info.
    :param info_extra:
        Added after the constructed info while it's still being used.
    :param info_color:
        The color to paint the info with (same as :param:`.color` if not specified).
    :param info_denominate:
        Used to determine the desired denomination of the value (and speed) and its respective unit.

        For example, if speed is :code:`'1000 KB/s'`, then :code:`denominate(1000)` may return :code:`(1000, 'MB')` so that speed is shown as :code:`1000/1000 -> '1 MB/s'` 
        
    |theme| :code:`.graphics.MultiLineProgressControl`
    """
    
    __slots__ = ('_total', '_runes', '_color', '_value', '_deque',
                 '_deque_limit_time', '_deque_first_time', 
                 '_info_value_template', '_info_speed_template',
                 '_info_chron_template', '_info_delimit', '_info_epilogue',
                 '_info_extra', '_info_color', '_info_denominate')

    @_theme.add('graphics.MultiLineProgressControl')
    def __init__(self, 
                 total              : _type_MultiLineProgressControl_init_total,
                 runes              : _type_MultiLineProgressControl_init_runes               = ('━',),
                 color              : _type_MultiLineProgressControl_init_color               = None,
                 value              : _type_MultiLineProgressControl_init_value               = 0,
                 deque_limit_size   : _type_MultiLineProgressControl_init_deque_limit_size    = 9999,
                 deque_limit_time   : _type_MultiLineProgressControl_init_deque_limit_time    = 3,
                 info_value_template: _type_MultiLineProgressControl_init_info_value_template = '{value}/{total}{unit}',
                 info_speed_template: _type_MultiLineProgressControl_init_info_speed_template = '{speed}{unit}/s',
                 info_chron_template: _type_MultiLineProgressControl_init_info_chron_template = '{remain}',
                 info_delimit       : _type_MultiLineProgressControl_init_info_delimit        = ' ',
                 info_epilogue      : _type_MultiLineProgressControl_init_info_epilogue       = None,
                 info_extra         : _type_MultiLineProgressControl_init_info_extra          = None,
                 info_color         : _type_MultiLineProgressControl_init_info_color          = _helpers.auto,
                 info_denominate    : _type_MultiLineProgressControl_init_info_denominate     = None):
        
        if info_color is _helpers.auto:
            info_color = color

        if info_denominate is None:
            info_denominate = lambda value: (1, '')

        self._total = total
        self._runes = runes
        self._color = color

        self._value = value

        self._deque = collections.deque(maxlen = deque_limit_size)
        self._deque_limit_time = deque_limit_time
        self._deque_first_time = None

        self._info_value_template = info_value_template
        self._info_speed_template = info_speed_template
        self._info_chron_template = info_chron_template
        self._info_delimit = info_delimit
        self._info_epilogue = info_epilogue
        self._info_extra = info_extra
        self._info_color = info_color
        self._info_denominate = info_denominate
        
    @property
    def value(self) -> _type_MultiLineProgressControl_init_value:
        
        """
        The internal value.
        """

        return self._value
    
    @property
    def deque(self) -> collections.deque[tuple[float, _type_MultiLineProgressControl_init_value]]:
        
        """
        The internal queue with ``(timestamp, addition)`` pairs.
        """

        return self._deque
    
    def move(self, 
             size: _type_MultiLineProgressControl_move_size):
        
        """
        Move the internal value.
        
        :param size:
            The amount to move it by.
        """
        
        new_size = size

        new_time = time.perf_counter()
        
        if self._deque_first_time is None:
            self._deque_first_time = new_time
        
        self._value += new_size

        spot = (new_time, new_size)
        
        for _ in range(2):
            try:
                self._deque.append(spot)
            except IndexError:
                self._deque.popleft()
                
        if self._deque_limit_time is None:
            return
        
        while self._deque:
            old_spot = self._deque[0]
            dif_time = new_time - old_spot[0]
            if dif_time < self._deque_limit_time:
                break
            self._deque.popleft()

    def get_line(self, 
                 width: _type_MultiLineProgressControl_get_line_width) -> str:
        
        """
        Get the current line text.
        
        :param width:
            The maximum amount of allowed characters.
        """

        ratio = width / self._total
        value = min(width, self._value * ratio)

        full_count = math.floor(value)

        result = self._runes[-1] * full_count

        if full_count < width:
            suffix_index = (value - full_count) * len(self._runes)
            suffix_index = math.floor(suffix_index)
            suffix = self._runes[suffix_index]
            result = result + suffix

        result = _helpers.paint_text(self._color, result)

        return result
    
    def _get_info_made_parts(self):

        total_deno, total_unit = self._info_denominate(self._total)

        value_prop = self._value / total_deno
        value_text = '{0:.0f}'.format(value_prop)

        total_prop = self._total / total_deno
        total_text = '{0:.0f}'.format(total_prop)
        
        yield self._info_value_template.format(value = value_text, total = total_text, unit = total_unit)
        
        if not self._deque:
            return
        
        old_time, old_size = self._deque[0]
        
        new_size = 0
        for new_time, sub_size in self._deque:
            new_size += sub_size
        
        elapse = new_time - self._deque_first_time
        elapse_text = _helpers.format_seconds(elapse, depth = 2)
        
        remain_time = new_time - old_time
        remain_size = new_size - old_size
        
        try:
            speed = remain_size / remain_time
        except ZeroDivisionError:
            speed = 0

        try:
            remain = max((self._total - self._value) / speed, 0)
        except ZeroDivisionError:
            remain_text = '??:??'
        else:
            remain_text = _helpers.format_seconds(remain, depth = 2)

        speed_deno, speed_unit = self._info_denominate(speed)
        speed = speed / speed_deno
        speed_text = f'{{0:.2f}}'.format(speed)
        
        yield self._info_speed_template.format(speed = speed_text, unit = speed_unit)
        
        yield self._info_chron_template.format(elapse = elapse_text, remain = remain_text)
        
    def _get_info_made(self):
        
        info_parts = self._get_info_made_parts()
        info_parts = list(info_parts)
        
        info_extra = _helpers.get_or_call(self._info_extra, self)

        if not info_extra is None:
            info_parts.append(info_extra)
        
        info = self._info_delimit.join(info_parts)
        
        return info
    
    def _get_info_done(self):
        
        epilogue = self._info_epilogue
        
        if epilogue is None:
            return self._get_info_made()
        
        epilogue = _helpers.get_or_call(epilogue, self)
        
        return epilogue
    
    def _get_info(self):
        
        if self._value < self._total:
            info = self._get_info_made()
        else:
            info = self._get_info_done()
        
        info = _helpers.paint_text(self._info_color, info)
        
        return info
    
    def get_info(self) -> str:
        
        """
        Get the current info text.
        
        Will be an empty string if the internal deque is empty
        """
        
        return self._get_info()
        

@_theme.add('graphics.LineProgress.prefix')
def _get_MultiLineProgress_prefix(self):
    
    pass


@_theme.add('graphics.LineProgress.suffix')
def _get_MultiLineProgress_suffix(progress, delimit = ' | '):
    
    infos = (control.get_info() for control in progress.controls)
    
    return ' ' + delimit.join(infos)


_type_MultiLineProgress_init_controls    = list[MultiLineProgressControl]
_type_MultiLineProgress_init_width       = _type_MultiLineProgressControl_get_line_width
_type_MultiLineProgress_init_empty       = str
_type_MultiLineProgress_init_prefix      = _type_init_Graphic_prefix
_type_MultiLineProgress_init_suffix      = _type_init_Graphic_suffix
_type_MultiLineProgress_init_prefix_wall = str
_type_MultiLineProgress_init_suffix_wall = str


class MultiLineProgress(Graphic):
    
    """
    A manager for progress controls.
    
    :param controls:
        The controls to manage.
    :param width:
        The default width for each line.
    :param empty:
        The rune to fill empty space with.
    :param prefix_wall:
        Added before the line.
    :param prefix_wall:
        Added after the line.

    .. code-block:: python

        total = 1600
        stages = {total * 1/4: 'stage 1', total * 2/4: 'stage 2', total * 3/4: 'stage 3'}
        # after each threshold, display the respective "stage"
        info_extra = lambda control: next((title for value, title in sorted(stages.items(), reverse = True) if control.value > value), None)
        # initialize the different "controls", each can be used completely separately to advance its respective line
        controls = [
            survey.graphics.MultiLineProgressControl(total, color = survey.colors.basic('blue' ), info_epilogue = 'done!'),
            survey.graphics.MultiLineProgressControl(total, color = survey.colors.basic('red'  ), info_extra    = info_extra),
            survey.graphics.MultiLineProgressControl(total, color = survey.colors.basic('green'), info_epilogue = lambda context: 'dynamic done!')
        ]
        # lower-index controls take longer to iterate, but speed up as the higher-index controls complete 
        with survey.graphics.MultiLineProgress(controls, prefix = 'Loading '):
            for _ in range(total):
                for index, control in enumerate(controls, start = 1):
                    if control.value >= total:
                        continue
                    for _ in range(index):
                        control.move(1)
                        time.sleep(0.01)
    
    |theme| :code:`graphics.MultiLineProgress`
    """
    
    __slots__ = ('_controls',)

    _interface_frequency = 0.1

    @_theme.add('graphics.MultiLineProgress')
    def __init__(self, 
                 controls   : _type_MultiLineProgress_init_controls, 
                 *args, 
                 width      : _type_MultiLineProgress_init_width       = 50,
                 empty      : _type_MultiLineProgress_init_empty       = ' ',
                 prefix     : _type_MultiLineProgress_init_prefix      = _get_MultiLineProgress_prefix,
                 suffix     : _type_MultiLineProgress_init_suffix      = _get_MultiLineProgress_suffix,
                 prefix_wall: _type_MultiLineProgress_init_prefix_wall = '|',
                 suffix_wall: _type_MultiLineProgress_init_suffix_wall = '|',
                 **kwargs):
        
        self._controls = controls

        def get(*args):
            rest_infos = []
            for control in controls:
                text = control.get_line(width)
                rest_line = _helpers.split_line(text)
                rest_time = control.deque[-1][0] if control.deque else 0
                rest_infos.append((rest_line, rest_time))
            main_line = list(empty * width)
            rank = lambda info: (len(info[0]), - info[1])
            for rest_line, _ in sorted(rest_infos, key = rank, reverse = True):
                main_line[0:len(rest_line)] = rest_line
            return prefix_wall + ''.join(main_line) + suffix_wall
        
        super().__init__(get, *args, prefix = prefix, suffix = suffix, **kwargs)
        
    @property
    def controls(self) -> _type_MultiLineProgress_init_controls:
        
        """
        The internal controls.
        
        Can be modified in any way at any time.
        """
        
        return self._controls
    
    
_type_LineProgress_init_total = _type_MultiLineProgressControl_init_total

_type_LineProgress_from_iterable_iterable = collections.abc.Container
_type_LineProgress_from_iterable_total    = typing.Union[_type_MultiLineProgressControl_init_total, None]
_type_LineProgress_from_iterable_count    = typing.Union[typing.Callable[[typing.Any], int], None]

_type_LineProgress_move_size = _type_MultiLineProgressControl_move_size


class LineProgress(MultiLineProgress):
    
    """
    A simple line progress with one internal control.
    
    :param total:
        The total expected value.

    .. code-block:: python

        total = 1600
        numbers = list(range(total))
        for number in survey.graphics.LineProgress.from_iterable(numbers, prefix = 'Loading ', info_epilogue = 'done!'):
            time.sleep(0.01)

    .. code-block:: python

        total = 1600
        numbers = list(range(total))
        with survey.graphics.LineProgress(len(numbers), prefix = 'Loading ', info_epilogue = 'done!') as progress:
            for number in numbers:
                time.sleep(0.01)
                progress.move(1)
    
    |theme| :code:`graphics.LineProgress`

    .. image:: /_static/images/graphics.lineprogress-1.gif
    """
    
    __slots__ = ()
    
    @_theme.add('graphics.LineProgress')
    def __init__(self, 
                 total: _type_LineProgress_init_total, 
                 *args, 
                 **kwargs):
        
        control_kwargs_names = _helpers.get_function_args_names(MultiLineProgressControl)
        control_kwargs = _helpers.yank_dict(kwargs, control_kwargs_names)
        control = MultiLineProgressControl(total, **control_kwargs)
        controls = (control,)
        
        super().__init__(controls, *args, **kwargs)
        
    @classmethod
    def from_iterable(cls, 
                      iterable: _type_LineProgress_from_iterable_iterable, 
                      *args, 
                      total   : _type_LineProgress_from_iterable_total = None, 
                      count   : _type_LineProgress_from_iterable_count = None, 
                      **kwargs):
        
        """
        Yields values from the iterable and displays the progress to completion.
        
        :param iterable:
            The iterable to yield values from.
        :param total:
            The total of the iterable if it cannot be determined directly from it.
        :param count:
            Can be used to specify by how much to increase the internal value per yield (default: ``1``).
            
        :raise TypeError: The iterable does not implement ``__len__`` and :paramref:`.total` has not been used.
        """

        if total is None:
            try:
                total = len(iterable)
            except TypeError as error:
                try:
                    total = iterable.__length_hint__()
                except AttributeError:
                    raise error
            
        if count is None:
            count = lambda value: 1
        
        with cls(total, *args, **kwargs) as self:
            for data in iterable:
                size = count(data)
                self._move(size)
                yield data

    @classmethod
    def from_response(cls, response, *args, **kwargs):

        """
        Yields chunks of data as received from the response.
        """

        total = int(response.headers['Content-length'])

        iterable = response.iter_content()
        
        units = ('B', 'KB', 'MB', 'GB')
        basic = 10 ** 3

        def denominate(value):
            for power, unit in reversed(tuple(enumerate(units))):
                ratio = basic ** power
                check = total / ratio
                if check > 1:
                    break
            return (ratio, unit)
        
        def count(data):
            return len(data)

        return cls.from_iterable(iterable, *args, total = total, info_denominate = denominate, count = count, **kwargs) 
        
    def _move(self, size):
        
        self._controls[0].move(size)
        
    def move(self, 
             size: _type_LineProgress_move_size):
        
        """
        Move the underlying control's value.
        
        :param size:
            Same as :paramref:`.MultiLineProgressControl.move`.
        """
        
        self._move(size)
        
        