Quickstart
==========

:func:`~survey.input` does exactly what you'd expect.

.. code-block:: py

    name = survey.input('ping? ')
    print(f'Answered {name}.')

.. image:: /_static/images/edit0.gif

Supporting line breaks can be done by passing ``multi = True``.

.. code-block:: py

    message = survey.input('Enter a commit message: ', multi = True)
    print(f'Answered with {len(message)} characters.')

.. image:: /_static/images/edit1.gif

:func:`~survey.password` should be used for obscuring input.

.. code-block:: py

    secret = survey.password('Password: ')
    print(f'Answered {secret}.')

.. image:: /_static/images/edit2.gif

:func:`~survey.confirm` helps with ``Y/N``\-type prompts returning :class:`bool`.

.. code-block:: py

    response = survey.confirm('Do you like pie? ', default = True)
    print(f'Answered {response}.')

.. image:: /_static/images/edit3.gif

:func:`~survey.question` can be paired with :func:`~survey.accept` or
:func:`~survey.reject` to convey affirmation.

.. code-block:: py

    guess = survey.question('Capital of Hungary: ')
    (survey.accept if guess == 'Budapest' else survey.reject)()

    hint = '\x1b[90m(fahrenheit)\x1b[0m ' # ansi color codes
    guess = survey.question('Burning point of paper: ', hint = hint)
    (survey.accept if guess == '451' else survey.reject)()

.. image:: /_static/images/edit4.gif

:func:`~survey.select` allows choice between options. Typing filters unsuitable options.

.. code-block:: py

    colors = ('red', 'green', 'blue')
    index = survey.select(colors, 'Pick a color: ')
    print(f'Answered {colors[index]}.')

.. image:: /_static/images/select0.gif

Multiple option selection can be done by passing ``multi = True``.

.. code-block:: py

    days = ('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')

    template = '\x1b[90m[filter: {0} | move: ↑↓ | pick: → all: →→ | unpick: ← all: ←←]\x1b[0m'
    instruct = 'type'

    def callback(event, indexes, *args):
        if event == 'filter':
            (value,) = args
            show = value or instruct
            hint = template.format(show)
            survey.update(hint)

    hint = template.format(instruct)
    indexes = survey.select(days, 'Favourite days? ', multi = True, hint = hint, limit = None, callback = callback)

    days = [days[index] for index in sorted(indexes)] # indexes is a set
    print(f'Answered {days}.')

.. image:: /_static/images/select1.gif

The last example is a bit more complicated for the sake of showcasing a bit more of what's possible.

Head over to :ref:`Reference` and dig into the finner details!
