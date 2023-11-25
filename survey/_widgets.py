
"""
Combinations of :class:`~.mutates.Mutate`\\s, :class:`~.visuals.Visual`\\s and 
:class:`~.handle.Handle` to create interactive units that can be resolved into expected values. 
"""

import contextvars
import datetime
import functools
import itertools
import math
import typing

from . import (_colors, _controls, _core, _funnels, _handle, _helpers,
               _mutates, _searches, _stage, _system, _theme, _visuals)

__all__ = ('Abort', 'Escape', 'Widget', 'start', 
           'BaseText', 'Input', 'Numeric', 'Conceal', 'AutoSubmit', 'Inquire', 
           'BaseMesh', 'BaseList', 'Select', 'Basket', 'Count', 'DateTime',
           'Form')


class Abort(_helpers.InfoErrorMixin, Exception):

    """
    Raised when an invokation needs to stop. May include a message.
    """

    __slots__ = ()


class Escape(Exception):

    """
    Raised when the users pressed the ``Esc`` button.
    """

    __slots__ = ()


_type_Widget_init_mutate    = _mutates.Mutate
_type_Widget_init_visual    = _visuals.Visual
_type_Widget_init_callback  = _handle._type_Handle_init_callback
_type_Widget_init_delegate  = typing.Callable[[_core.Event], bool]
_type_Widget_init_validate  = typing.Callable[[typing.Any], None]
_type_Widget_init_escapable = bool

_type_Widget_invoke_event = _core.Event
_type_Widget_invoke_info  = _core._type_ansi_parse_return


class Widget:

    """
    A team of mutate, handle and visual working together.

    :param mutate:
        The underlying mutate for changing data.
    :param visual:
        The underlying visual for fetching drawing information.
    :param callback:
        Used as :paramref:`.handle.Handle.callback`.
    :param delegate:
        Used with ``(event)`` and decides whether to continue the invokation.
    :param validate:
        Used with ``(result)`` upon submission, forbidden by raising :exc:`.Abort`.
    """

    _product_mark = object()

    __slots__ = ('_mutate', '_handle', '_visual', '_delegate', '_validate', '_escapable', '_product')

    def __init_subclass__(cls, controls = (), **kwargs):

        pre_controls = getattr(cls, '_controls', ())
        
        cls._controls = (*pre_controls, *controls)

        super().__init_subclass__(**kwargs)

    def __init__(self, 
                 mutate   : _type_Widget_init_mutate, 
                 visual   : _type_Widget_init_visual, 
                 callback : _type_Widget_init_callback  = None, 
                 delegate : _type_Widget_init_delegate  = None,
                 validate : _type_Widget_init_validate  = None,
                 escapable: _type_Widget_init_escapable = False):
        
        self._delegate = delegate
        self._validate = validate
        self._product = self._product_mark

        self._mutate = mutate

        handle = _handle.Handle(mutate, callback = callback)

        for control in self._controls:
            handle.add(control)

        self._handle = handle
        self._visual = visual

        self._escapable = escapable

    @property
    def mutate(self):

        """
        The underlying mutate.
        """

        return self._mutate
    
    def _prepare(self, value):

        return value
    
    def _produce(self):

        raise NotImplemented()
    
    def _resolve(self):

        value = self._product

        if value is self._product_mark:
            value = self._produce()
            value = self._prepare(value)

        return value
    
    def resolve(self):

        """
        Get the resolved value.
        """

        return self._resolve()
    
    def _invoke_validate(self):

        validate = self._validate

        if validate is None:
            return

        value = self._product

        if value is self._product_mark:
            value = self._product = self._produce()

        try:
            validate(value)
        except Abort:
            self._product = self._product_mark
            raise

    def _invoke(self, event, *args, **kwargs):

        if self._delegate and not self._delegate(event):
            return

        try:
            self._handle.invoke(event, *args, **kwargs)
        except _core.Terminate:
            self._invoke_validate(); raise
    
    def invoke(self, 
               event: _type_Widget_invoke_event, 
               info : _type_Widget_invoke_info):
        
        """
        Invoke the underlying handle.

        :param event:
            Dictates the type of operation.
        :param info:
            Contains details used during the operation.

        .. note::

            If :paramref:`.delegate` is provided and returns :code:`False`, nothing happens.
        """

        if self._escapable and event == _core.Event.escape:
            raise Escape()

        self._invoke(event, info)
    
    def _sketch(self, *args, **kwargs):

        return self._visual.get(*args, **kwargs)
    
    def sketch(self, 
               *args, 
               **kwargs) -> _visuals._type_Visual_get_return:

        """
        Get the lines and point used for rendering the widget's state.

        Additional arguments are passed to the underlying :meth:`.Visual.get` method.

        :return:
            The ``(lines, point)`` that can be used to draw.
        """
        
        return self._sketch(*args, **kwargs)


def _start_variant_parse(parse, value):
    if parse:
        lines = _helpers.split_lines(value)
        point_y = len(lines) - 1
        point_x = len(lines[point_y])
        point = [point_y, point_x]
        value = (lines, point)
    return value


_type_start_get_actor_contextual_parse   = bool
_type_start_get_actor_contextual_context = contextvars.ContextVar


def _start_get_actor_contextual(parse  : _type_start_get_actor_contextual_parse,
                                context: _type_start_get_actor_contextual_context):

    def wrapper(*args, **kwargs):
        value = context.get()
        return _start_variant_parse(parse, value)
    
    return wrapper


_type_start_start_get_actor_static_parse = _type_start_get_actor_contextual_parse
_type_start_start_get_actor_static_value = typing.Union[str, typing.List[typing.List[str]]]


def _start_get_actor_static(parse: _type_start_start_get_actor_static_parse, 
                            value: _type_start_start_get_actor_static_value):

    context = contextvars.ContextVar('state')

    context.set(value)

    wrapper = _start_get_actor_contextual(parse, context)

    return wrapper


_type_start_start_get_actor_dynamic_parse = _type_start_get_actor_contextual_parse
_type_start_start_get_actor_dynamic_fetch = typing.Callable[[typing.Any], typing.Tuple[_visuals._type_Text_link_lines, _visuals._type_Text_link_point]]


def _start_get_actor_dynamic(parse: _type_start_start_get_actor_dynamic_parse, 
                             fetch: _type_start_start_get_actor_dynamic_fetch):

    context = contextvars.ContextVar('state')

    def updater(*args, **kwargs):
        context.set(fetch(*args, **kwargs))
    
    wrapper = _start_get_actor_contextual(parse, context)

    return wrapper, updater


_type_start_get_actor_dichotomic_parse = _type_start_get_actor_contextual_parse
_type_start_get_actor_dichotomic_value = typing.Union[_type_start_start_get_actor_static_value, _type_start_start_get_actor_dynamic_fetch]


def _start_get_actor_dichotomic(parse: _type_start_get_actor_dichotomic_parse, 
                                value: _type_start_get_actor_dichotomic_value):

    if callable(value):
        wrapper, updater = _start_get_actor_dynamic(parse, value)
    else:
        wrapper = _start_get_actor_static(parse, value)
        updater = _helpers.noop

    return wrapper, updater


_start_warn_reset_lines = [[]]

_type_start_multi_pre  = _stage._type_get_multi_maybe
_type_start_multi_aft  = bool
_type_start_widget     = Widget
_type_start_show       = typing.Union[str, None]
_type_start_mark       = typing.Union[str, None]
_type_start_mark_color = str
_type_start_info       = typing.Union[_type_start_get_actor_dichotomic_value, None]
_type_start_info_parse = _type_start_get_actor_dichotomic_parse
_type_start_hint       = typing.Union[_type_start_get_actor_dichotomic_value, None]
_type_start_hint_parse = _type_start_get_actor_dichotomic_parse
_type_start_site       = _stage._type_get_site
_type_start_reply      = typing.Union[typing.Callable[[Widget, typing.Any], str], None]


def _start(multi_pre : _type_start_multi_pre, 
           multi_aft : _type_start_multi_aft,
           widget    : _type_start_widget, 
           show      : _type_start_show       = None,
           mark      : _type_start_mark       = '? ',
           mark_color: _type_start_mark_color = _colors.basic('yellow'),
           info      : _type_start_info       = None,
           info_parse: _type_start_info_parse = True,
           hint      : _type_start_hint       = None, 
           hint_parse: _type_start_hint_parse = True,
           site      : _type_start_site       = 'body',
           reply     : _type_start_reply      = None):
    
    """
    Start a widget and return its resolve result upon submission.

    :param multi_pre:
        Whether the body should start on a separate line during use.
    :param multi_aft:
        Whether the reply should start on a separate line.
    :param widget:
        The widget to use.
    :param show:
        Printed before anything else (uncontrollable).
    :param mark:
        Prepended to the ``show``.
    :parm mark_color:
        The color to paint ``mark`` with.
    :param info:
        The info for the stage. If callable, takes ``(widget, event_name, event_info)``.
    :param info_parse:
        Whether ``info`` is given (or, if callable returns) as a :class:`str` or ``(lines, point)``.
    :param hint:
        The hint for the stage. If callable, takes ``(widget, event_name, event_info)``.
    :param hint_parse:
        Whether ``hint`` is given (or, if callable returns) as a :class:`str` or ``(lines, point)``.
    :param site:
        Can be :code:`'info'` or :code:`'body'` to place the cursor on the info or widget body respectively.
    :param reply:
        Called upon successful submission with ``(widget, result)``. Should return a class:`str` that is used as a response.
    """

    if not show is None:
        if not mark is None:
            if mark_color:
                mark = _helpers.paint_text(mark_color, mark)
            show = mark + show
        show_get = _start_get_actor_static(True, show)
        _system.screen.print(show_get, False, learn = False)

    if info is None:
        info = ''

    if hint is None:
        hint = ''

    info_get, info_update = _start_get_actor_dichotomic(info_parse, info)
    hint_get, hint_update = _start_get_actor_dichotomic(hint_parse, hint)
    body_get = widget.sketch

    multi_pre_maybe = multi_pre
    multi_pre_force = bool(show)

    visual = _stage.get(multi_pre_maybe, multi_pre_force, site, info_get, hint_get, body_get)

    def sketch(*args, **kwargs):
        return visual.get(*args, **kwargs)
    
    update = _helpers.chain_functions(info_update, hint_update)

    memory = result = None
    
    def invoke(*args, **kwargs):
        nonlocal memory, result
        memory = widget.mutate.get_state()
        try:
            try:
                widget.invoke(*args, **kwargs)
            except _core.Terminate:
                result = widget.resolve()
                raise
            else:
                _stage.warn(_start_warn_reset_lines)
                update(widget, *args, **kwargs)
        except _mutates.Error:
            _system.io.ring()
            raise _core.SkipDraw()
        except Abort as error:
            widget.mutate.set_state(memory)
            message = error.text
            if not message is None:
                lines = _helpers.split_lines(message)
                _stage.warn(lines)
            _system.io.ring()

    update(widget, None, None) # emulate

    try:
        _system.console.start(sketch, invoke)
    except BaseException:
        _system.cursor.clear(); raise

    def sketch():
        if reply is None:
            lines = []
        else:
            value = reply(widget, result)
            lines = _start_variant_parse(True, value)[0]
        if multi_aft and not show is None:
            lines.insert(0, [])
        lines.append([])
        return (lines, None)
    _system.screen.print(sketch, True)

    return result


start = _start


_type_BaseText_init_lines        = _mutates._type_Text_init_lines 
_type_BaseText_init_point        = _mutates._type_Text_init_point
_type_BaseText_init_multi        = bool
_type_BaseText_init_callback     = _type_Widget_init_callback
_type_BaseText_init_delegate     = _type_Widget_init_delegate
_type_BaseText_init_validate     = _type_Widget_init_validate
_type_BaseText_init_escapable    = _type_Widget_init_escapable
_type_BaseText_init_funnel_enter = _visuals._type_Text_init_funnel_enter
_type_BaseText_init_funnel_leave = _visuals._type_Text_init_funnel_leave


_BaseText_controls = (
    _controls.text_insert,
    _controls.text_move_left,
    _controls.text_move_right,
    _controls.text_move_up,
    _controls.text_move_down,
    _controls.text_delete_left,
    _controls.text_delete_right,
    _controls.text_newline
)


class BaseText(Widget, controls = _BaseText_controls):

    """
    Base for text-like widgets.

    :param lines:
        Same as :paramref:`.mutates.Text.lines`.
    :param point:
        Same as :paramref:`.mutates.Text.point`.
    :param multi:
        Whether to support multiple lines. If so, leaving 2 empty lines submits.
    :param callback:
        Same as :paramref:`.Widget.callback`.
    :param delegate:
        Same as :paramref:`.Widget.delegate`.
    :param validate:
        Same as :paramref:`.Widget.validate`.
    :param funnel_enter:
        Same as :paramref:`.visuals.Text.funnel_enter`.
    :param funnel_leave:
        Same as :paramref:`.visuals.Text.funnel_leave`.
    """

    __slots__ = ()

    def __init__(self, 
                 lines       : _type_BaseText_init_lines, 
                 point       : _type_BaseText_init_point,
                 multi       : _type_BaseText_init_multi        = False,
                 callback    : _type_BaseText_init_callback     = None,
                 delegate    : _type_BaseText_init_delegate     = None,
                 validate    : _type_BaseText_init_validate     = None,
                 escapable   : _type_BaseText_init_escapable    = False,
                 funnel_enter: _type_BaseText_init_funnel_enter = None, 
                 funnel_leave: _type_BaseText_init_funnel_leave = None):

        mutate = _mutates.Text(lines, point)

        def visual_get(*args):
            return (mutate.lines, mutate.point)

        visual = _visuals.Text(visual_get, funnel_enter, funnel_leave)

        handle = _handle.Handle()
        
        if not multi:
            @handle.add
            @_controls.get((_handle.EventType.enter, _core.Event.enter))
            def handle_entry(info):
                raise _core.Terminate()
            
        callback = _helpers.chain_functions(callback, handle.invoke)

        super().__init__(
            mutate, 
            visual,
            callback = callback,
            delegate = delegate,
            validate = validate,
            escapable = escapable
        )


_type_Input_init_value = str
_type_Input_init_index = int


class Input(BaseText):

    """
    A text editor.

    It resolves into a :class:`str`.

    :param value:
        Converted into :paramref:`.BaseText.lines`.
    :param index:
        Where to place in the cursor in relation to its position along the continous text. Converted into :paramref:`.BaseText.point`. 

    Arguments directly passed to super-class:
    
        - :paramref:`~.BaseText.lines` - Created from :paramref:`.value`.
        - :paramref:`~.BaseText.point` - Created from :paramref:`.index`.

    |theme| :code:`'widgets.Input'`.
    """

    __slots__ = ()

    @_theme.add('widgets.Input')
    def __init__(self, 
                 *args,
                 value: _type_Input_init_value = _helpers.auto, 
                 index: _type_Input_init_index = _helpers.auto,
                 **kwargs):
        
        if value is _helpers.auto:
            value = ''
        
        if index is _helpers.auto:
            index = len(value)

        lines = _helpers.split_lines(value)

        y, x = _helpers.text_index_to_point(lines, index)

        point = [y, x]

        super().__init__(lines, point, *args, **kwargs)

    def _produce(self):

        value = _helpers.join_lines(self._mutate.lines)

        return value
    

_type_Numeric_init_value                 = int
_type_Numeric_init_decimal               = bool
_type_Numeric_init_zfill                 = int
_type_Numeric_init_invalid_value_message = str


class Numeric(Input):

    """
    A text editor that only allows submission with numeric values.

    It resolves into a :class:`int` or :class:`float`.

    :param value:
        Converted into :paramref:`.Input.value`.
    :param decimal:
        Whether to allow (finite) decimal values.
    :param zfill:
        Amount of 0-fill to have.
    :param invalid_value_message:
        Used as template to raise :exc:`.Abort` when the value is invalid.

    Arguments directly passed to super-class:
    
        - :paramref:`~.Input.value` - Created from :paramref:`.value`.

    |theme| :code:`'widgets.Numeric'`.
    """

    @staticmethod
    def _transform_float(abort_message, value):
        try:
            value = float(value)
        except ValueError:
            raise Abort(abort_message)
        if math.isinf(value):
            raise Abort(abort_message)
        return value
    
    @staticmethod
    def _transform_int(abort_message, value):
        try:
            value = int(value)
        except ValueError:
            raise Abort(abort_message)
        return value
    
    __slots__ = ('_transform', '_transform_abort_message')

    @_theme.add('widgets.Numeric')
    def __init__(self, 
                 *args,
                 value                : _type_Numeric_init_value                 = _helpers.auto,
                 decimal              : _type_Numeric_init_decimal               = False,
                 zfill                : _type_Numeric_init_zfill                 = 0,
                 invalid_value_message: _type_Numeric_init_invalid_value_message = 'invalid {name}',
                 **kwargs):
        
        super_cls = self.__class__.__mro__[1]

        funnel_leave = _helpers.get_function_arg_safe(super_cls, 'funnel_leave', kwargs, pop = True)
        
        if not value is _helpers.auto:
            value = str(value)

        if decimal:
            transform = self._transform_float
            abort_message_space = {'name': 'float'} 
        else:
            transform = self._transform_int
            abort_message_space = {'name': 'int'}

        self._transform = transform
        self._transform_abort_message = None if invalid_value_message is None else invalid_value_message.format(**abort_message_space)

        funnel_leave_group = []
        funnel_leave_entry = _funnels.text_min_horizontal(_funnels.JustType.end, zfill, '0')
        funnel_leave_group.append(funnel_leave_entry)
        funnel_leave = _helpers.chain_functions(*funnel_leave_group, funnel_leave)

        super().__init__(
            *args,
            value = value,
            funnel_leave = funnel_leave,
            **kwargs
        )

    def _produce(self):

        value = super()._produce()

        if value == '-':
            value = '0'

        if value.endswith('.'):
            value = f'{value}0'

        value = self._transform(self._transform_abort_message, value)

        return value


_type_Conceal_init_rune  = str
_type_Conceal_init_color = typing.Union[int, None]


class Conceal(Input):

    """
    A text editor that replaces all characters with a rune.

    It resolves into a :class:`str`.

    :param rune:
        The rune to replace all others with.
    :param color:
        The color to paint the rune with.

    |theme| :code:`'widgets.Conceal'`.
    """

    __slots__ = ()

    @_theme.add('widgets.Conceal')
    def __init__(self, 
                 *args, 
                 rune : _type_Conceal_init_rune  = '*', 
                 color: _type_Conceal_init_color = None, 
                 **kwargs):

        super_cls = self.__class__.__mro__[1]

        funnel_leave = _helpers.get_function_arg_safe(super_cls, 'funnel_leave', kwargs, pop = True)

        funnel_leave_group = []
        funnel_leave_entry = _funnels.text_replace(rune)
        funnel_leave_group.append(funnel_leave_entry)
        if not color is None:
            funnel_leave_entry = _funnels.text_paint(color)
            funnel_leave_group.append(funnel_leave_entry)
        funnel_leave = _helpers.chain_functions(*funnel_leave_group, funnel_leave)

        super().__init__(*args, funnel_leave = funnel_leave, **kwargs)


_type_AutoSubmit_init_evaluate  = typing.Callable[[str], None]
_type_AutoSubmit_init_validate  = typing.Callable[[str], bool]
_type_AutoSubmit_init_default   = typing.Any
_type_AutoSubmit_init_transform = typing.Union[typing.Callable[[str], str], None]


class AutoSubmit(Input):

    """
    A text editor that automatically submits a upon valid insertion.

    Resolves into a :class:`str`.

    :param evaluate:
        Used with ``(result)`` before insertion, which can be prevented by raising :exc:`.Abort` (like :paramref:`.Widget.validate`).
    :param validate:
        Used with ``(result)`` after to decide whether to submit (should return :cls:`bool`).
    :param default:
        Used instead when attempting to submit without a value.
    :param transform:
        Used with ``(result)`` and should return a new ``result`` used for checks.

    Arguments directly passed to super-class:
    
        - :paramref:`~.Input.validate` - Set to :code:`None`.
    """

    __slots__ = ()

    _default_mark = _helpers.auto

    def __init__(self, 
                 evaluate : _type_AutoSubmit_init_evaluate,
                 validate : _type_AutoSubmit_init_validate,
                 *args,
                 default  : _type_AutoSubmit_init_default   = _default_mark, 
                 transform: _type_AutoSubmit_init_transform = None,
                 **kwargs):
        
        super_cls = self.__class__.__mro__[1]

        callback = _helpers.get_function_arg_safe(super_cls, 'callback', kwargs, pop = True)
    
        handle = _handle.Handle()

        @handle.add
        @_controls.get((_handle.EventType.enter, _core.Event.enter))
        def _control_submit_enter(info):
            if _helpers.check_lines(self._mutate.lines) or default is self._default_mark:
                raise Abort(None)
            self._product = default
            raise _core.Terminate()

        _state = NotImplemented
        
        @handle.add
        @_controls.get((_handle.EventType.enter, _core.Event.insert))
        def _control_insert_enter(info):
            nonlocal _state
            _state = self._mutate.get_state()

        @handle.add
        @_controls.get((_handle.EventType.leave, _core.Event.insert))
        def _control_insert_leave(info):
            value = super(AutoSubmit, self)._produce()
            if not transform is None:
                value = transform(value)
            try:
                evaluate(value)
            except Abort:
                self._mutate.set_state(_state); raise
            if not validate(value):
                return
            self._product = value
            raise _core.Terminate()
        
        callback = _helpers.chain_functions(callback, handle.invoke)

        super().__init__(
            *args, 
            validate = None,
            callback = callback,
            **kwargs
        )
            

_type_Inquire_init_options  = typing.Dict[str, typing.Any]
_type_Inquire_init_tranform = _type_AutoSubmit_init_transform
    

class Inquire(AutoSubmit):

    """
    A text editor that submits upon insertion of an option.

    Resolves into the value of the matching option.

    :param options:
        The possible options. Attempting to insert a rune that does not lead to an option is forbidden. 
    :param transform:
        Used on all options and the current value when comparing.

    Arguments directly passed to super-class:
    
        - :paramref:`~.AutoSubmit.evaluate` - Created using :paramref:`.options`.
        - :paramref:`~.AutoSubmit.validate` - Created using :paramref:`.options`.

    |theme| :code:`'widgets.Inquire'`.
    """

    __slots__ = ('_options',)

    @_theme.add('widgets.Inquire')
    def __init__(self, 
                 *args,
                 options  : _type_Inquire_init_options  = {'y': True, 'n': False}, 
                 transform: _type_Inquire_init_tranform = str.lower,
                 **kwargs):

        if not transform is None:
            options = dict(zip(map(transform, options), options.values()))

        self._options = options
        
        def evaluate(value):
            for option in options:
                if option.startswith(value):
                    return
            raise Abort(None)
        
        def validate(value):
            return value in options
        
        super().__init__(
            evaluate, 
            validate, 
            *args, 
            transform = transform,
            **kwargs
        )

    def _prepare(self, value):

        value = super()._prepare(value)

        value = self._options[value]

        return value
    
    
def _focus_nil(spot):

    return False


def _focus_all(spot): 

    return True


def _get_mesh_point(axis, index, default = 0):

    return _helpers.get_axis_point(2, axis, default, index)


def _get_mesh_spot(*args, **kwargs):

    point = _get_mesh_point(*args, **kwargs)

    return tuple(point)


_type_BaseMesh_init_search       = _mutates._type_Mesh_init_score
_type_BaseMesh_init_create       = _mutates._type_Mesh_init_create
_type_BaseMesh_init_tiles        = _mutates._type_Mesh_init_tiles
_type_BaseMesh_init_point        = _mutates._type_Mesh_init_point
_type_BaseMesh_init_clean        = _mutates._type_Mesh_init_clean
_type_BaseMesh_init_scout        = _mutates._type_Mesh_init_scout
_type_BaseMesh_init_rigid        = _mutates._type_Mesh_init_rigid
_type_BaseMesh_init_focus        = typing.Union[bool, typing.Callable[[_core.Event], bool] ]
_type_BaseMesh_init_callback     = _type_Widget_init_callback
_type_BaseMesh_init_delegate     = _type_Widget_init_delegate
_type_BaseMesh_init_validate     = _type_Widget_init_validate
_type_BaseMesh_init_escapable    = _type_Widget_init_escapable
_type_BaseMesh_init_funnel_enter = _visuals._type_Mesh_init_funnel_enter
_type_BaseMesh_init_funnel_leave = _visuals._type_Mesh_init_funnel_leave


_BaseMesh_controls = (
    _controls.mesh_move_left,
    _controls.mesh_move_right,
    _controls.mesh_move_up,
    _controls.mesh_move_down,
    _controls.mesh_insert,
    _controls.mesh_delete,
    _controls.mesh_enter
)


class BaseMesh(Widget, controls = _BaseMesh_controls):

    """
    A mesh traverser.

    :param search:
        Same as :paramref:`.mutates.Mesh.score`.
    :param create:
        Same as :paramref:`.mutates.Mesh.create`.
    :param tiles:
        Same as :paramref:`.mutates.Mesh.tiles`. Values should be :class:`Widget` instances.
    :param point:
        Same as :paramref:`.mutates.Mesh.point`.
    :param clean:
        Same as :paramref:`.mutates.Mesh.clean`.
    :param scout:
        Same as :paramref:`.mutates.Mesh.scout`.
    :param rigid:
        Same as :paramref:`.mutates.Mesh.rigid`.
    :param focus:
        When :class:`bool`, it is used as the initial focus state. The state can be set to :code:`True` with :attr:`.Event.indent` while unfocused, and to :code:`False` by submitting the focused tile.
        When :class:`~typing.Callable`, it is used on each invokation to determine whether to delegate it to the currently pointed-at tile instead.
    :param callback:
        Same as :paramref:`.Widget.callback`.
    :param delegate:
        Same as :paramref:`.Widget.delegate`.
    :param validate:
        Same as :paramref:`.Widget.validate`.
    :param escapable:
        Same as :paramref:`.Widget.escapable`.
    :param funnel_enter:
        Same as :paramref:`.visuals.Mesh.funnel_enter`.
    :param funnel_leave:
        Same as :paramref:`.visuals.Mesh.funnel_leave`.
    """

    __slots__ = ('_focus',)

    def __init__(self, 
                 tiles       : _type_BaseMesh_init_tiles        = _helpers.auto, 
                 point       : _type_BaseMesh_init_point        = _helpers.auto, 
                 create      : _type_BaseMesh_init_create       = None,
                 search      : _type_BaseMesh_init_search       = _searches.fuzzy,
                 clean       : _type_BaseMesh_init_clean        = False,
                 scout       : _type_BaseMesh_init_scout        = None, 
                 rigid       : _type_BaseMesh_init_rigid        = False,
                 focus       : _type_BaseMesh_init_focus        = False,
                 callback    : _type_BaseMesh_init_callback     = None,
                 delegate    : _type_BaseMesh_init_delegate     = None,
                 validate    : _type_BaseMesh_init_validate     = None,
                 escapable   : _type_BaseMesh_init_escapable    = True,
                 funnel_enter: _type_BaseMesh_init_funnel_enter = None, 
                 funnel_leave: _type_BaseMesh_init_funnel_leave = None):
        
        if tiles is _helpers.auto:
            tiles = ()

        tiles = dict(tiles)
        
        if point is _helpers.auto:
            try:
                point_spot = min(tiles)
            except ValueError:
                point = [0, 0]
            else:
                point = list(point_spot)

        mutate = _mutates.Mesh(search, scout, rigid, create, clean, tiles, point)

        def visual_get(*args):
            tiles = {}
            for vis_spot, cur_spot in mutate.vision.items():
                try:
                    tile = mutate.tiles[cur_spot]
                except KeyError:
                    continue
                tiles[vis_spot] = tile.sketch(*args)
            point = mutate.point
            return (tiles, point)

        visual = _visuals.Mesh(visual_get, funnel_enter, funnel_leave)

        self._focus = focus

        super().__init__(
            mutate, 
            visual,
            escapable = escapable,
            validate = validate,
            delegate = delegate,
            callback = callback
        )

    @property
    def focus(self):

        return self._focus

    @property
    def _focusable(self):

        return not callable(self._focus)
    
    def _invoke_blear(self, *args, **kwargs):

        super()._invoke(*args, **kwargs)

    def _handle_focus(self):

        self._focus = not self._focus
        
    def _invoke_focus(self, *args, **kwargs):

        tile = self._mutate.cur_tile

        try:
            tile.invoke(*args, **kwargs)
        except _core.Terminate:
            if self._focusable:
                self._handle_focus()
                if not self._focus:
                    return
            raise

    def _invoke(self, event, *args, **kwargs):

        switcher = self._focusable
        delegate = self._focus if switcher else self._focus(event)

        if delegate:
            self._invoke_focus(event, *args, **kwargs)
        elif switcher and event is _core.Event.indent:
            self._handle_focus()
        else:
            self._invoke_blear(event, *args, **kwargs)


_type_BaseList_init_tiles       = typing.Union[typing.List[Widget], _type_BaseMesh_init_tiles]
_type_BaseList_init_axis        = int
_type_BaseList_init_delimit     = str
_type_BaseList_init_index       = int
_type_BaseList_init_label       = typing.Union[typing.Callable[[int], str], None]
_type_BaseList_init_view_max    = typing.Union[int, None]
_type_BaseList_init_focus_color = typing.Union[str, None]
_type_BaseList_init_focus_mark  = typing.Union[str, None]
_type_BaseList_init_evade_color = typing.Union[str, None]
_type_BaseList_init_evade_mark  = typing.Union[str, None]
_type_BaseList_init_fill        = bool


_BaseList_controls = (
    _controls.mesh_move_up_reverse,
    _controls.mesh_move_down_reverse,
)


class BaseList(BaseMesh, controls = _BaseList_controls):

    """
    Base for list-like widgets.

    Resolves to a :class:`int` (the pointed index).

    :param axis:
        Denotes the axis across which movement is allowed.
    :param tiles:
        Same as :paramref:`.BaseMesh.tiles`, but it can be any iterable.
    :param index:
        Used as the :paramref:`.axis`\\th element of :paramref:`.BaseMesh.point`.
    :param label:   
        Used as ``(index, tile)`` and returns a label to place on the right. 
    :param view_max:
        Maximum amount of elemnts visible at once.
    :param focus_color:
        The color to paint the current tile with.
    :param focus_mark:  
        The rune to prepend to the current tile.
    :param evade_color:
        The color to paint the non-current tiles with.
    :param evade_mark:
        The rune to prepend to the non-current tiles.
    :param fill:
        Whether to fill empty room.
    :param delimit:
        The rune inserted between tiles.

    Arguments directly passed to super-class:
    
        - :paramref:`~.BaseMesh.tiles` - Created using :paramref:`.tiles`.
        - :paramref:`~.BaseMesh.point` - Created using :paramref:`.index`.

    .. warning::
        For the sake of matching each spot's index to it's ``axis``\\-th value, vertical movement and vision are
        adjusted so that indexes increment downward instead of upward (which is how :class:`.BaseMesh` behaves normally).
    """
        
    __slots__ = ('_axis',)

    def __init__(self,
                 *args,
                 axis       : _type_BaseList_init_axis        = 0,
                 tiles      : _type_BaseList_init_tiles       = _helpers.auto,
                 index      : _type_BaseList_init_index       = 0,
                 label      : _type_BaseList_init_label       = None,
                 view_max   : _type_BaseList_init_view_max    = 7,
                 focus_color: _type_BaseList_init_focus_color = _colors.basic('cyan'),
                 focus_mark : _type_BaseList_init_focus_mark  = '> ',
                 evade_color: _type_BaseList_init_evade_color = None,
                 evade_mark : _type_BaseList_init_evade_mark  = '  ',
                 fill       : _type_BaseList_init_fill        = True,
                 delimit    : _type_BaseList_init_delimit     = None,
                 **kwargs):
        
        self._axis = axis
        
        super_cls = self.__class__.__mro__[1]

        if tiles is _helpers.auto:
            tiles = ()
        
        if not isinstance(tiles, dict):
            tiles = {_get_mesh_spot(axis, index): tile for index, tile in enumerate(tiles)}
        
        point = _get_mesh_point(axis, index)

        funnel_enter = _helpers.get_function_arg_safe(super_cls, 'funnel_enter', kwargs, pop = True)
        
        funnel_enter_group = []

        if not axis:
            funnel_enter_entry = _funnels.mesh_flip(axis)
            funnel_enter_group.append(funnel_enter_entry)

        if not view_max is None:
            if not view_max > 1:
                focus_mark = None 
            funnel_enter_entry = _funnels.mesh_max(axis, view_max)
            funnel_enter_group.append(funnel_enter_entry)

        if not delimit is None:
            funnel_enter_entry = _funnels.mesh_delimit(axis, delimit)
            funnel_enter_group.append(funnel_enter_entry)

        funnel_enter_entry = _funnels.mesh_light(focus_color, evade_color)
        funnel_enter_group.append(funnel_enter_entry)

        if focus_mark is None:
            focus_mark = ''

        if evade_mark is None:
            evade_mark = ''

        if not axis:
            funnel_enter_entry = _funnels.mesh_point(focus_mark, evade_mark)
            funnel_enter_group.append(funnel_enter_entry)

        if not label is None:
            def funnel_enter_entry_get(index):
                spot = _get_mesh_spot(axis, index)
                tile = self._mutate.tiles.get(spot)
                value = label(index, tile)
                lines = _helpers.split_lines(value)
                return lines
            funnel_enter_entry = _funnels.mesh_head(axis, funnel_enter_entry_get, _funnels.JustType.start)
            funnel_enter_group.append(funnel_enter_entry)

        if fill:
            funnel_enter_entry = _funnels.mesh_grid_fill()
            funnel_enter_group.append(funnel_enter_entry)

        funnel_enter = _helpers.chain_functions(*funnel_enter_group, funnel_enter)

        super().__init__(
            *args,
            tiles = tiles,
            point = point,
            funnel_enter = funnel_enter,
            **kwargs
        )

    @property
    def axis(self):

        return self._axis

    def _produce(self):

        index = self._mutate.cur_spot[self._axis]

        return index


_type_Select_init_options = typing.List[str]
_type_Select_init_create  = typing.Union[typing.Callable[[_mutates._type_Mesh_init_spot], str], None]
_type_Select_init_Option  = Input


class Select(BaseList):

    """
    A single-option selector.

    :param options:
        Converted into :paramref:`.BaseList.tiles`.
    :param create:
        Same as :paramref:`.BaseMesh.create`, except returned values are converted to widgets.
    :param Option:
        Used to convert :paramref:`.options` and :paramref:`.create` results to tiles.

    Arguments directly passed to super-class:
    
        - :paramref:`~.BaseList.tiles` - Created using :paramref:`.options`.
        - :paramref:`~.BaseList.create` - Created using :paramref:`.create`.
        - :paramref:`~.BaseList.focus` - Set to a :class:`~typing.Callable` that delegates no events.
        - :paramref:`~.BaseList.delimit` - Defaults to :code:`' '` when :paramref:`.BaseList.axis` is set to :code:`1`.

    Arguments used for :paramref:`.Option`:

        - :paramref:`~.Input.value` - Set to each option upon creation.

    |theme| :code:`'widgets.Select'`.
    """

    __slots__ = ()

    @_theme.add('widgets.Select')
    def __init__(self, 
                 *args,
                 options: _type_Select_init_options = _helpers.auto,
                 create : _type_Select_init_create  = None,
                 Option : _type_Select_init_Option  = Input,
                 **kwargs):
        
        super_cls = self.__class__.__mro__[1]
        
        axis = _helpers.get_function_arg_safe(super_cls, 'axis', kwargs)

        if axis:
            kwargs.setdefault('delimit', ' ')
        
        def get_tile(value):
            option = Option(
                value = value
            )
            return option
        
        if options is _helpers.auto:
            options = ()
        
        tiles = map(get_tile, options)

        def create(spot, *, __sub = create):
            if __sub is None:
                return None
            value = __sub(spot)
            if not isinstance(value, Widget):
                tile = get_tile(value)
            return tile

        super().__init__(
            *args,
            tiles = tiles, 
            create = create,
            focus = _focus_nil,
            **kwargs
        )


_type_Basket_init_options       = typing.List[str]
_type_Basket_init_active        = typing.List[int]
_type_Basket_init_positive_mark = str
_type_Basket_init_negative_mark = str
_type_Basket_init_Option        = Input
_type_Basket_init_Stamp         = Select


_Basket_directional_events = {
    0: (_core.Event.arrow_left, _core.Event.arrow_right),
    1: (_core.Event.arrow_down, _core.Event.arrow_up)
}

_Basket_search_get = lambda tile: tile.mutate.tiles[(0, 1)].sketch()


class Basket(BaseList):

    """
    A multi-item selector.

    :param options:
        Converted into :paramref:`.BaseList.tiles`.
    :param active:
        Indexes that should be selected from the start.
    :param positive_mark:
        Prepended to all selected options.
    :param negative_mark:
        Prepended to all non-selected options.
    :param Option:
        Used to convert :paramref:`.options` to tiles.
    :param Stamp:
        Used to convert :paramref:`.positive_mark` or :paramref:`.negative_mark` to tiles.
    
    Arguments directly passed to super-class:
    
        - :paramref:`~.BaseList.tiles` - Created using :paramref:`.options`.
        - :paramref:`~.BaseList.focus` - Set to a :class:`~typing.Callable` that delegates arrow events based on axis.
        - :paramref:`~.BaseList.delimit` - Defaults to :code:`' '` when :paramref:`.BaseList.axis` is set to :code:`1`

    Arguments used for :paramref:`.Option`:

        - :paramref:`~.Input.value` - Set to each option upon creation.

    Arguments used for :paramref:`.Stamp`:

        - :paramref:`~.Select.axis` - Set to to the opposite of :paramref:`.BaseList.axis`.
        - :paramref:`~.Select.options` - Set to a :class:`tuple` of :paramref:`.negative_mark` and :paramref:`.positive_mark`
        - :paramref:`~.BaseList.index` - Set to either :code:`0` or :code:`1` depending on whether the option's index is in :paramref:`.active`.
        - :paramref:`~.BaseList.view_max` - Set to :code:`1`.
        - :paramref:`~.BaseList.focus_color` - Set to :code:`None`.
        - :paramref:`~.Widget.callback` - Set to a :class:`~typing.Callable` that handles multi-switching of marks.

    |theme| :code:`'widgets.Basket'`.
    """

    @_theme.add('widgets.Basket')
    def __init__(self,
                 *args,
                 options      : _type_Basket_init_options       = _helpers.auto, 
                 active       : _type_Basket_init_active        = _helpers.auto,
                 positive_mark: _type_Basket_init_positive_mark = '[X]', 
                 negative_mark: _type_Basket_init_negative_mark = '[ ]',
                 Option       : _type_Basket_init_Option        = Input, 
                 Stamp        : _type_Basket_init_Stamp         = Select,
                 **kwargs):
        
        super_cls = self.__class__.__mro__[1]

        axis = _helpers.get_function_arg_safe(super_cls, 'axis', kwargs)
        axis_refl = int(not axis)

        if axis:
            kwargs.setdefault('delimit', ' ')

        if options is _helpers.auto:
            options = ()
        
        if active is _helpers.auto:
            active = set()

        search = _helpers.get_function_arg_safe(super_cls, 'search', kwargs, pop = True)

        if not search is None:
            search = functools.partial(search, get = _Basket_search_get)

        axis_events = _Basket_directional_events[axis]

        stamp_handle = _handle.Handle()

        def _control_function_arrow(forward, info):
            cur_tile = self._mutate.cur_tile
            cur_spot = cur_tile.mutate.cur_tile.mutate.cur_spot
            cur_mark = cur_spot[axis_refl]
            if not (forward and cur_mark or not forward and not cur_mark):
                return
            for oth_spot in self._mutate.vision.values():
                oth_tile = self._mutate.tiles[oth_spot]
                if oth_tile is cur_tile:
                    continue
                oth_tile.mutate.cur_tile.mutate.point[axis_refl] = cur_mark
            raise _handle.Abort()
        
        for event_index, event in enumerate(axis_events):
            partial = functools.partial(_control_function_arrow, event_index)
            control = _controls.get((_handle.EventType.enter, event))(partial)
            stamp_handle.add(control)

        create_sub = _helpers.get_function_arg_safe(super_cls, 'create', kwargs, pop = True)
        
        def get_widget(index, value):
            stamp_widget_options = (negative_mark, positive_mark)
            stamp_widget_index = int(index in active)
            stamp_widget = Stamp(
                options = stamp_widget_options, 
                axis = axis_refl, 
                index = stamp_widget_index,
                view_max = 1, 
                focus_color = None,
                callback = stamp_handle.invoke
            )
            value_widget = Option(
                value = value
            )
            main_widget_tiles = (stamp_widget, value_widget)
            main_widget = BaseList(
                tiles = main_widget_tiles, 
                axis = 1,
                focus = True,
                focus_color = None,
                delimit = ' '
            )
            return main_widget

        tiles = itertools.starmap(get_widget, enumerate(options))

        def create(index):
            if create_sub is None:
                return None
            value = create_sub(index)
            widget = get_widget(index, value)
            return widget
        
        def focus(event):
            return event in axis_events
        
        super().__init__(
            *args,
            tiles  = tiles, 
            create = create, 
            search = search, 
            focus  = focus,
            **kwargs)

    def _produce(self):

        indexes = set()
        for spot, tile in self._mutate.tiles.items():
            # row.mutate.stamp.mutate.cur_spot
            if not tile.mutate.cur_tile.mutate.cur_spot[1]:
                continue
            index = spot[self._axis]
            indexes.add(index)
        
        return indexes


_type_Count_init_value   = typing.Union[int, float]
_type_Count_init_rate    = typing.Union[int, float]
_type_Count_init_convert = typing.Union[typing.Callable[[_type_Count_init_value], _type_Count_init_value], None]
_type_Count_init_decimal = typing.Union[bool, None]
_type_Count_init_Numeric = Numeric
    

_Count_focus_events = {
    _core.Event.insert, _core.Event.delete_left
}

_Count_focus = lambda event: event in _Count_focus_events
    

class Count(BaseList):

    """
    An editable counter.

    Resolves to an :class:`int` (the pointed value).

    :param value:
        Initial value.
    :param rate:
        Rate to move by.
    :param decimal:
        Whether to only allow :class:`float` or :class:`int`.
    :param convert:
        Used with ``(value)`` before creating a new widget.
    :param Numeric:
        Used to convert each value into a widget.

    Arguments directly passed to super-class:
    
        - :paramref:`~.BaseList.axis` - Set to :code:`0`.
        - :paramref:`~.BaseList.index` - Set to :code:`0` (:paramref:`.value` is used as an offset).
        - :paramref:`~.BaseList.clean` - Set to :code:`True`.
        - :paramref:`~.BaseList.create` - Created from :paramref:`.value`, :paramref:`.rate`, :paramref:`.decimal` and :paramref:`.convert`. 
        - :paramref:`~.BaseList.focus` - Set to a :class:`~typing.Callable` that delegates :attr:`~.Event.insert` and :attr:`~.Event.delete_left`.
        - :paramref:`~.BaseList.focus_mark` - Set to a :code:`None`.

    Arguments used for :paramref:`.Numeric`:

        - :paramref:`~.Numeric.value` - Set to each numeric value upon creation.
        - :paramref:`~.Numeric.decimal` - Set to :class:`float` unless :paramref:`.decimal` specifies otherwise.

    |theme| :code:`'widgets.Count'`.
    """

    __slots__ = ('_decimal',)

    @_theme.add('widgets.Count')
    def __init__(self,
                 *args,
                 value  : _type_Count_init_value   = 0,
                 rate   : _type_Count_init_rate    = 1,
                 decimal: _type_Count_init_decimal = None,
                 convert: _type_Count_init_convert = None,
                 Numeric: _type_Count_init_Numeric = Numeric,
                 **kwargs):
        
        self._decimal = decimal
        
        offset = value
        
        def create(spot):
            value = offset - sum(spot) * rate
            decimal = self._decimal
            if decimal is None:
                decimal = True
            if not convert is None:
                value = convert(value) 
            tile = Numeric(
                value = value, 
                decimal = decimal
            )
            return tile
        
        super().__init__(
            *args,
            axis = 0,
            index = 0,
            clean = True,
            create = create,
            focus = _Count_focus,
            focus_mark = None,
            **kwargs
        )

    def _produce(self):

        value_any = self._mutate.cur_tile.resolve()
        value_int = int(value_any)

        if self._decimal is None and value_int == value_any:
            value_any = value_int

        return value_any
    

_DateTime_focus_events = {
    _core.Event.arrow_up, _core.Event.arrow_down,
    _core.Event.insert, _core.Event.delete_left
}


_DateTime_focus = lambda event: event in _DateTime_focus_events


_DateTime_funnel_enter_arrange_attr_groups = (
    ('year', 'month', 'day'),
    ('hour', 'minute', 'second')
)


def _DateTime_funnel_enter_arrange(axis, attrs, date_delimit, time_delimit, part_delimit, tiles, point):

    delimits = (date_delimit, time_delimit)

    stores = ([], [])

    for attr in attrs:
        for attr_group_index, attr_group in enumerate(_DateTime_funnel_enter_arrange_attr_groups):
            if not attr in attr_group:
                continue
            break
        else:
            raise ValueError(f'invalid attribute: {attr}')
        stores[attr_group_index].append(attr)

    index = 0
    last_tiles = {}
    roll_tiles = {}

    for some_attrs, some_delimit in zip(stores, delimits):
        if not some_attrs:
            continue
        some_tiles = {}
        for index in range(index, len(some_attrs) + index):
            spot = _get_mesh_spot(axis, index)
            tile = tiles[spot]
            some_tiles[spot] = tile
        _funnels.mesh_delimit.call(axis, some_delimit, some_tiles, None)
        try:
            max_spot = max(last_tiles)
            min_spot = min(some_tiles)
        except ValueError:
            pass
        else:
            roll_tiles[max_spot] = last_tiles[max_spot]
            roll_tiles[min_spot] = some_tiles[min_spot]
        index += 1
        last_tiles = some_tiles

    if not roll_tiles:
        return
    
    _funnels.mesh_delimit.call(axis, part_delimit, roll_tiles, None)


_Datetime_zfills = {
    'year'  : 4,
    'month' : 2,
    'day'   : 2,
    'hour'  : 2,
    'minute': 2,
    'second': 2
}


_type_DateTime_init_value        = datetime.datetime
_type_DateTime_init_Chron        = Count
_type_DateTime_init_attrs        = typing.List[str]
_type_DateTime_init_date_delimit = str
_type_DateTime_init_time_delimit = str
_type_DateTime_init_part_delimit = str


class DateTime(BaseList):

    """
    A datetime picker.

    Resolves to :class:`datetime.datetime` object.

    :param value:
        Initial value.
    :param attrs:
        The :class:`datetime` attributes used.
    :param Chron:
        Used to convert :paramref:`.value` to tiles.
    :param date_delimit:
        Separator for date parts.
    :param time_delimit:
        Separator for time parts.
    :param part_delimit:
        Separator for the date and time parts.

    Arguments directly passed to super-class:
    
        - :paramref:`~.BaseList.axis` - Set to :code:`1`.
        - :paramref:`~.BaseList.tiles` - Created from :paramref:`.value`'s attributes using :paramref:`.attrs` and :paramref:`.Chron`.
        - :paramref:`~.BaseMesh.focus` - Set to a :class:`~typing.Callable` that delegates :attr:`~.Event.arrow_up`, :attr:`~.Event.arrow_down`, :attr:`~.Event.insert` and :attr:`~.Event.delete_left`. 

    Arguments used for :paramref:`.Chron`:

        - :paramref:`~.Count.value` - Set to each numeric value for each part.
        - :paramref:`~.Count.decimal` - Set to :code:`False`.
        - :paramref:`~.Count.convert` - Set to a :class:`~typing.Callable` that returns the rolling :class:`datetime.datetime`\'s value after attempting to set it.
        - :paramref:`~.Count.Numeric` - Set to a partial :class:`.Numeric` (see later for arguments).
        - :paramref:`~.BaseList.focus_color` - Set to :code:`None`.

    Arguments used for :paramref:`.Chron`\'s :paramref:`~.Count.Numeric`:

        - :paramref:`~.Numeric.zfill` - Set to the maximum amount of digits for the respective part.

    |theme| :code:`'widgets.DateTime'`.
    """

    __slots__ = ('_datetime', '_datetime_attrs')

    @_theme.add('widgets.DateTime')
    def __init__(self,
                 *args,
                 value       : _type_DateTime_init_value        = None,
                 attrs       : _type_DateTime_init_attrs        = ('day', 'month', 'year', 'hour', 'minute'),
                 Chron       : _type_DateTime_init_Chron        = Count,
                 date_delimit: _type_DateTime_init_date_delimit = '/',
                 time_delimit: _type_DateTime_init_time_delimit = ':',
                 part_delimit: _type_DateTime_init_part_delimit = ' ',
                 **kwargs):
        
        super_cls = self.__class__.__mro__[1]
        
        funnel_enter = _helpers.get_function_arg_safe(super_cls, 'funnel_enter', kwargs, pop = True)

        axis = 1
        
        if value is None:
            value = datetime.datetime.now()

        self._datetime = value

        self._datetime_attrs = attrs

        def get_tile(attr):
            def convert(value):
                kwargs = {attr: value}
                self._datetime = self._convert(kwargs)
                return str(value)
            zfill = _Datetime_zfills.get(attr, 0)
            chron = Chron(
                value = getattr(value, attr),
                decimal = False,
                convert = convert,
                Numeric = functools.partial(
                    Numeric, 
                    zfill = zfill
                ),
                focus_color = None
            )
            return chron
        
        tiles = []
        for attr in attrs:
            tile = get_tile(attr)
            tiles.append(tile)

        funnel_enter_group = []

        funnel_enter_entry = functools.partial(
            _DateTime_funnel_enter_arrange,
            axis, attrs, date_delimit, time_delimit, part_delimit,
        )
        funnel_enter_group.append(funnel_enter_entry)

        funnel_enter = _helpers.chain_functions(funnel_enter, *funnel_enter_group)

        super().__init__(
            *args,
            axis = 1,
            tiles = tiles,
            focus = _DateTime_focus,
            funnel_enter = funnel_enter,
            **kwargs
        )

    @property
    def attrs(self):

        return self._datetime_attrs
    
    def _convert(self, kwargs, value = None):

        try:
            datetime = self._datetime.replace(**kwargs)
        except ValueError as error: 
            message = str(error)
            if not value is None:
                message += f' ({value})'
            raise Abort(message)
        
        return datetime

    def _produce(self):

        kwargs = {}
        for index, name in enumerate(self._datetime_attrs):
            spot = _get_mesh_spot(self._axis, index)
            tile = self._mutate.tiles[spot]
            value = tile.resolve()
            kwargs[name] = value

        value = self._convert(kwargs)

        return value
    

_Form_tile_focus = lambda event: True
    

class Form(BaseList):

    """
    A multi-item form.

    :param form:
        A mapping of ``field: editable widget`` pairs.
    :param Field:
        Used to convert :paramref:`.form` keys to tiles.
    :param delimit:
        Placed between fields and widgets.

    Arguments directly passed to super-class:
    
        - :paramref:`~.BaseList.axis` - Set to :code:`1`
        - :paramref:`~.BaseList.tiles` - Created using :paramref:`.form`.
        - :paramref:`~.BaseList.focus_color` - Set to :code:`None`.
        - :paramref:`~.BaseList.evade_color` - Set to :code:`None`.

    Arguments used for :paramref:`.Field`:

        - :paramref:`~.Input.value` - Set to each pair's field.
        - :paramref:`~.Input.funnel_leave` - Set to a :class:`~typing.Callable` that aligns with others fields and includes :paramref:`.delimit`.

    |theme| :code:`'widgets.Form'`.
    """

    @_theme.add('widgets.Form')
    def __init__(self, 
                 *args, 
                 form = {},
                 Field = Input, 
                 delimit = ':',
                 **kwargs):
        
        super_cls = self.__class__.__mro__[1]
        
        form = dict(form)

        def tile_focus(*args):
            return _Form_tile_focus(*args)
        
        focus_color = _helpers.get_function_arg_safe(super_cls, 'focus_color', kwargs, pop = True)
        evade_color = _helpers.get_function_arg_safe(super_cls, 'evade_color', kwargs, pop = True)
                    
        def get_tile_focus_color(index):
            def focus_color_get():
                if not self._mutate.cur_spot[0] == index:
                    return None
                return focus_color
            return focus_color_get
        
        def get_tile_evade_color(index):
            def evade_color_get():
                if not self._mutate.cur_spot[0] == index:
                    return None
                return evade_color
            return evade_color_get
        
        top_field_size = max(map(len, form))

        def get_tile(index, field, value_widget):
            field_funnel_leave_group = []
            field_funnel_leave_entry = _funnels.text_min_horizontal(_funnels.JustType.end, top_field_size, ' ')
            field_funnel_leave_group.append(field_funnel_leave_entry)
            field_funnel_leave_entry = _funnels.text_bloat_horizontal(_funnels.JustType.start, 1, delimit)
            field_funnel_leave_group.append(field_funnel_leave_entry)
            field_funnel_leave = _helpers.chain_functions(*field_funnel_leave_group)
            field_widget = Field(
                value = field,
                funnel_leave = field_funnel_leave
            )
            tile_widgets = (field_widget, value_widget)
            tile = BaseList(
                axis = 1,
                index = 1,
                tiles = tile_widgets,
                focus = tile_focus,
                focus_color = get_tile_evade_color(index),
                evade_color = get_tile_focus_color(index),
                delimit = ' '
            )
            return tile
        
        tiles = []
        for index, item in enumerate(form.items()):
            tile = get_tile(index, *item)
            tiles.append(tile)

        super().__init__(
            *args,
            axis = 0,
            tiles = tiles,
            focus_color = None,
            evade_color = None,
            **kwargs
        )

    def _produce(self):

        form = {}
        for tile in self.mutate.tiles.values():
            field_widget = tile.mutate.tiles[(0, 0)]
            field = field_widget.resolve()
            value_widget = tile.mutate.tiles[(0, 1)]
            value = value_widget.resolve()
            form[field] = value

        return form
