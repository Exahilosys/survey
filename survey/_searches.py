
"""
Functions that can be used directly for :paramref:`.mutates.Mesh.score`.
"""

import itertools


__all__ = ('fuzzy',)


_fuzzy_mark = object()


def fuzzy(argument, tile, get = lambda tile: tile.sketch(False, False)):

    (lines, point) = get(tile)

    cur_line = itertools.chain.from_iterable(lines)
    cur_line = map(str.lower, cur_line)
    cur_line = list(cur_line)
    may_line = itertools.chain.from_iterable(argument)
    may_line = map(str.lower, may_line)

    score = 0
    density = 0
    for (may_index, may_rune) in enumerate(may_line):
        try:
            cur_index = cur_line.index(may_rune)
        except ValueError:
            return None
        score += 1
        density -= abs(may_index - cur_index)
        cur_line[cur_index] = _fuzzy_mark

    return (score, density)