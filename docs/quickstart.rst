Quickstart
==========

Examples to get you started right away!

Simple
------

- :func:`~survey.input` does exactly what you'd expect.

.. code-block:: py

    name = survey.input('ping? ')
    print(f'Answered {name}.')

.. image:: /_static/images/edit0.gif

- Supporting line breaks can be done by passing ``multi = True``.

.. code-block:: py

    message = survey.input('Enter a commit message: ', multi = True)
    print(f'Answered with {len(message)} characters.')

.. image:: /_static/images/edit1.gif

- :func:`~survey.password` should be used for obscuring input.

.. code-block:: py

    secret = survey.password('Type your password: ')
    print(f'Answered {secret}.')

.. image:: /_static/images/edit2.gif

- :func:`~survey.confirm` helps with ``Y/N``\-type prompts returning :class:`bool`.

.. code-block:: py

    response = survey.confirm('Do you like pie? ', default = True)
    print(f'Answered {response}.')

.. image:: /_static/images/edit3.gif

- :func:`~survey.question` can be paired with :func:`~survey.accept` or :func:`~survey.reject` to convey affirmation.

.. code-block:: py

    guess = survey.question('Capital of Hungary: ')
    survey.accept(guess == 'Budapest')

    hint = '(fahrenheit) '
    guess = survey.question('Burning point of paper: ', hint = hint)
    survey.accept(guess == '451')

.. image:: /_static/images/edit4.gif

- :func:`~survey.select` allows choice between options. Typing filters unsuitable options.

.. code-block:: py

    colors = ('red', 'green', 'blue')
    index = survey.select(colors, 'Pick a color: ')
    print(f'Answered {colors[index]}.')

.. image:: /_static/images/select0.gif

- Multiple option selection can be done by passing ``multi = True``.

.. code-block:: py

    days = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    indexes = survey.select(days, 'Favourite days? ', multi = True, limit = 4)
    print(f'Answered {indexes}.')

.. image:: /_static/images/select1.gif

- :func:`~survey.path` leverages :func:`~survey.traverse` to walk across file systems.

.. code-block:: py

    path = survey.path('./Sys', 'File: ')
    print(f'Answered {path}.')

.. image:: /_static/images/path0.gif

Advanced
--------

- Edit a file by setting the initial ``value`` to something.

.. code-block:: py

    with open('./main.py') as file:
        text = file.read()

    result = survey.input('Edit: ', multi = True, value = text)

    with open('./main.py', 'w') as file:
        file.write(result)

    print(f'Wrote {len(result)} characters.')

.. image:: /_static/images/edit5.gif

- Use ``callback`` with :class:`wrapio.Track` to listen to events and update info.

.. code-block:: py

    import wrapio

    track = wrapio.Track()

    limit = 50

    @track.call('insert')
    @track.call('delete')
    def handle(result, *args):
        remain = max(0, limit - len(result))
        info = str(remain)
        if remain < limit // 3:
            info = '\x1b[31m' + info + '\x1b[0m' # paint red
        survey.update(info)

    info = str(limit)
    hint = ' chars left'
    message = survey.input('Enter a commit message: ', info = info, hint = hint, multi = True, limit = limit, callback = track.invoke)
    print(f'Answered with {len(message)} characters.')

Flickering is caused by the cursor attempting to re-draw the info. Should not occur often.

.. image:: /_static/images/edit6.gif

- Use ``jump`` to auto-focus and enable ``TAB`` skipping.

.. code-block:: py

    stages = ('./Sys', './Sys/Absolute', './Sys/Absolute/Logarithms', './Sys/Absolute/Logarithms/Semaphoric')

    def jump(path, names):
        path = path.rstrip('/')
        try:
            index = stages.index(path)
            stage = stages[index + 1]
        except (ValueError, IndexError):
            return (None, None)
        name = os.path.basename(stage)
        index = names.index(name)
        return (index, name)

    path = survey.path(stages[0], allow = allow)

.. image:: /_static/images/path1.gif

- Customize general behavior (`colors <https://en.wikipedia.org/wiki/ANSI_escape_code#Colors>`_).

.. code-block:: py

    theme = survey.Theme(
        symbol = survey.Symbol(
            note = '! '
        ),
        palette = survey.Palette(
            note = '\x1b[33m', # yellow fg
            info = '\x1b[35m'  # magenta fg
        )
    )

    days = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')

    with survey.use(theme):
        indexes = survey.select(
            days,
            'Favourite days? ',
            multi = True,
            limit = 4,
            indent = 0,
            funnel = lambda i, v: v.upper(),
            prefix = '~ ',
            unpin = '[\x1b[31m✕\x1b[0m] ', # green fg + null
            pin = '[\x1b[32m✓\x1b[0m] ', # red fg + null
            color = '\x1b[33m', # yellow fg
            indexes = {1, 2, 4},
            check = lambda indexes: not 4 in indexes,
            hint = '(cannot submit with friday)'
        )

    print(f'Answered {indexes}.')

.. image:: /_static/images/theme.gif

Head over to :ref:`Reference` and dig into the finer details!
