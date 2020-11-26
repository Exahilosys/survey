import wrapio

from . import api
from . import helpers

from . import _colors


__all__ = ()


def _get_last_color(check, value):

    parts = helpers.seq.split(value)

    last = None
    for (index, part) in enumerate(parts):
        if index % 2 and part.endswith('m'):
            last = part
        elif check(part):
            break

    return last


class hint:

    def confirm(template,
                default = None,
                options = ('n', 'y'),
                inflate = True,
                color = _colors.info):

        """
        Create a hint for :func:`confirm` tool.

        :param str template:
            Should include 2 indexed formatting placeholders.
        :param bool default:
            Use to indicate if any option should be highlighted.
        :param list[str] options:
            2-length list containing negative and positive option respectively.
        :parm bool inflate:
            Whether to use :meth:`str.upper` on highlighted option.
        :param str color:
            Used for highlighting.
        """

        options = list(options)

        if not default is None:
            index = int(default)
            option = options[index]
            if inflate:
                option = option.upper()
            if color:
                check = lambda part: '{0}' in part
                last = _get_last_color(check, template)
                option = color + option + (last or _colors.null)
            options[index] = option
            if default is True:
                options = reversed(options)

        result = template.format(*options)

        return result

    def select(template,
               default = 'type',
               external = False,
               color = _colors.info):

        """
        Create a callback and hint for :func:`select` tool.

        :param str template:
            Should include up to one formatting placeholder for filter value.
        :param str default:
            Used when filter value is empty instead.
        :param bool external:
            Whether ``default`` should be used at all.
        :param str color:
            Used for highlighting filter value.

        Use the callback for automatically updating hint.
        """

        check = lambda part: '{0}' in part
        last = _get_last_color(check, template)

        def choose(value):
            if not value:
                return '' if external else default
            return color + value + (last or _colors.null)

        def format(value):
            show = choose(value)
            return template.format(show)

        track = wrapio.Track()

        @track.call
        def filter(result, value):
            hint = format(value)
            api.update(hint)

        hint = format('')

        return (track.invoke, hint)
