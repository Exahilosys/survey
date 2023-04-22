import collections

from . import _core


__all__ = ()


Control = collections.namedtuple('Control', 'event function')


def _control(event):

    def decorator(function):
        return Control(event, function)

    return decorator


get = _control


@_control(_core.Event.insert)
def text_insert(mutate, info):

    runes = (info.rune,)

    mutate.insert(runes)

    size = len(runes)

    mutate.move_x(size)


@_control(_core.Event.arrow_left)
def text_move_left(mutate, info):

    size = - 1

    mutate.move_x(size)


@_control(_core.Event.arrow_right)
def text_move_right(mutate, info):

    size = 1

    mutate.move_x(size)


@_control(_core.Event.arrow_up)
def text_move_up(mutate, info):

    size = - 1

    mutate.move_y(size)


@_control(_core.Event.arrow_down)
def text_move_down(mutate, info):

    size = 1

    mutate.move_y(size)


@_control(_core.Event.delete_left)
def text_delete_left(mutate, info):

    size = 1

    mutate.move_x(- size)
    mutate.delete(size)


@_control(_core.Event.delete_right)
def text_delete_right(mutate, info):

    size = 1

    mutate.delete(size)


def done(lines, point):

    cur_y = point[0]
    fin_y = len(lines) - 1
    
    return cur_y == fin_y and len(lines) > 2 and not any(lines[-2:])


@_control(_core.Event.enter)
def text_newline(mutate, info):
    lines = mutate.lines
    point = mutate.point
    if done(lines, point):
        lines[-2:] = ()
        y = len(lines) - 1
        x = len(lines[y])
        mutate.point[:] = (y, x)
        raise _core.Terminate()
    mutate.newline()


@_control(_core.Event.arrow_left)
def mesh_move_left(mutate, info):

    direction = 180

    mutate.move(direction)


@_control(_core.Event.arrow_right)
def mesh_move_right(mutate, info):

    direction = 0

    mutate.move(direction)


@_control(_core.Event.arrow_up)
def mesh_move_up(mutate, info):

    direction = + 90

    mutate.move(direction)


@_control(_core.Event.arrow_down)
def mesh_move_down(mutate, info):

    direction = - 90

    mutate.move(direction)


@_control(_core.Event.arrow_up)
def mesh_move_up_reverse(mutate, info):

    direction = - 90

    mutate.move(direction)


@_control(_core.Event.arrow_down)
def mesh_move_down_reverse(mutate, info):

    direction = + 90

    mutate.move(direction)


@_control(_core.Event.insert)
def mesh_insert(mutate, info):

    runes = (info.rune,)

    mutate.search_insert(runes)


@_control(_core.Event.delete_left)
def mesh_delete(mutate, info):

    size = 1

    mutate.search_delete(size)


@_control(_core.Event.enter)
def mesh_enter(mutate, info):

    raise _core.Terminate()

