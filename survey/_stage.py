
"""
Utilities for a :class:`~.visuals.Visual` that facilitates the main execution ground 
for  class:`.~widgets.Widget` by providing dynamic chunks of information around the screen.
"""

import typing
import copy

from . import _helpers
from . import _colors
from . import _visuals
from . import _funnels
from . import _system


__all__ = ('get', 'warn')


_warn_lines = [[]]


def _funnel_text_linesep(force, pre):

    def funnel(lines, point):
        if not force and not len(lines) > 1 and not any(lines):
            return
        if pre:
            lines.insert(0, [''])
            point[0] += 1
        else:
            lines.append([''])
    
    return funnel


_type_get_multi_maybe = bool
_type_get_multi_force = bool
_type_get_site        = str
_type_get_info_get    = _visuals._type_Text_init_get
_type_get_hint_get    = _visuals._type_Text_init_get
_type_get_body_get    = _visuals._type_Text_init_get
_type_get_info_color  = str
_type_get_hint_color  = str
_type_get_warn_color  = str


def _get(multi_maybe: _type_get_multi_maybe,
         multi_force: _type_get_multi_force, 
         site       : _type_get_site,
         info_get   : _type_get_info_get,
         hint_get   : _type_get_hint_get,
         body_get   : _type_get_body_get,
         info_color : _type_get_info_color = _colors.basic('cyan'), 
         hint_color : _type_get_hint_color = _colors.basic('black'), 
         warn_color : _type_get_warn_color = _colors.basic('red')):

    """
    Create a stage visual.

    :param multi_maybe:
        Whether the body may start on a separate line from the info and hint.
    :param multi_force:
        Whether the body has to start on a separate line from the info and hint.
    :param site:
        Can be :code:`'info'` or :code:`'body'` to place the cursor on the info or body respectively.
    :param info_get:
        Used to fetch info ``(lines, point)``.
    :param hint_get:
        Used to fetch hint ``(lines, point)``.
    :param body_get:
        Used to fetch body ``(lines, point)``.
    :param info_color:
        The color to paint info with.
    :param hint_color:
        The color to paint hint with.
    :param warn_color:
        The color to paint warn with.
    """

    global _warn_lines
    
    warn_lines = _warn_lines = [[]]
    
    info_funnel_leave_group = []
    info_funnel_leave_entry = _funnels.text_paint(info_color)
    info_funnel_leave_group.append(info_funnel_leave_entry)
    def info_funnel_leave_entry(lines, point):
        if not site == 'info' and not any(lines):
            return
        _funnels.text_bloat_horizontal.call(_funnels.JustType.start, 1, ' ', lines, point)
    info_funnel_leave_group.append(info_funnel_leave_entry)
    info_funnel_leave = _helpers.chain_functions(*info_funnel_leave_group)
    info_visual = _visuals.Text(info_get, funnel_leave = info_funnel_leave)

    hint_funnel_leave_group = []
    hint_funnel_leave_entry = _funnels.text_paint(hint_color)
    hint_funnel_leave_group.append(hint_funnel_leave_entry)
    hint_funnel_leave = _helpers.chain_functions(*hint_funnel_leave_group)
    hint_visual = _visuals.Text(hint_get, funnel_leave = hint_funnel_leave)

    warn_funnel_leave_group = []
    warn_funnel_leave_entry = _funnels.text_paint(warn_color)
    warn_funnel_leave_group.append(warn_funnel_leave_entry)
    warn_funnel_leave = _helpers.chain_functions(*warn_funnel_leave_group)
    warn_visual = _visuals.Text.link(warn_lines, [0, 0], funnel_leave = warn_funnel_leave)

    info_visual_get = info_visual.get
    hint_visual_get = hint_visual.get

    head_visual_tiles = {(0, 0): info_visual_get, (0, 1): hint_visual_get}
    head_funnel_enter_group = []
    head_funnel_entry_entry = _funnels.mesh_grid_fill()
    head_funnel_enter_group.append(head_funnel_entry_entry)
    head_funnel_enter = _helpers.chain_functions(*head_funnel_enter_group)
    head_funnel_leave_group = []
    if multi_maybe:
        head_funnel_leave_entry = _funnel_text_linesep(multi_force, False)
        head_funnel_leave_group.append(head_funnel_leave_entry)
    head_funnel_leave = _helpers.chain_functions(*head_funnel_leave_group)
    head_visual = _visuals.Mesh.link(head_visual_tiles, [0, 0], funnel_enter = head_funnel_enter, funnel_leave = head_funnel_leave)

    body_visual = _visuals.Text(body_get)

    foot_visual_tiles = {(0, 0): warn_visual.get}
    foot_funnel_enter = head_funnel_enter
    foot_funnel_leave_group = []
    foot_funnel_leave_entry = _funnel_text_linesep(False, True)
    foot_funnel_leave_group.append(foot_funnel_leave_entry)
    foot_funnel_leave = _helpers.chain_functions(*foot_funnel_leave_group)
    foot_visual = _visuals.Mesh.link(foot_visual_tiles, [0, 0], funnel_enter = foot_funnel_enter, funnel_leave = foot_funnel_leave)

    head_visual_get = head_visual.get
    body_visual_get = body_visual.get
    foot_visual_get = foot_visual.get

    main_visual_tiles = [head_visual_get, body_visual_get, foot_visual_get]

    main_visual_point_latch_group = {
        'info': head_visual_get,
        'body': body_visual_get
    }

    main_visual_point_latch = main_visual_point_latch_group[site]
    main_visual_point_index = main_visual_tiles.index(main_visual_point_latch)
    main_visual_point = [main_visual_point_index]

    main_funnel_leave_group = []
    # main_funnel_leave_entry = _funnels.text_max_dynamic(_system.cursor.measure)
    # main_funnel_leave_group.append(main_funnel_leave_entry)
    main_funnel_leave = _helpers.chain_functions(*main_funnel_leave_group)

    main_visual = _visuals.Line.link(main_visual_tiles, main_visual_point, funnel_leave = main_funnel_leave)

    return main_visual


get = _get


_type_warn_lines = _visuals._type_Text_link_lines


def _warn(lines: _type_warn_lines):

    """
    Create a warning udnerneath the body.

    :param lines:
        The warning lines.
    """

    _warn_lines[:] = copy.deepcopy(lines)


warn = _warn