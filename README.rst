✨ A simple library for creating beautiful interactive prompts.

.. image:: https://github.com/Exahilosys/survey/raw/master/images/showcase.gif

.. code-block:: py

    import survey

    name = survey.input('Username: ')
    password = survey.password('Password: ')
    actions = ('Call', 'Text', 'Exit')
    index = survey.select(actions, 'Chose an action: ')
    # if index == 0: elif index == 1: else: ...
    contacts = ('Squig', 'Zelan', 'Momo', 'Hamberg', 'Evan', 'Vonnie', 'Dwalon', 'Hacen')
    indexes = survey.select(contacts, 'Select recipients: ', multi = True)
    message = survey.input('Type messsage: ', multi = True)
    confirm = survey.confirm(f'Message is {len(message)} characters long. Send? ', default = True)

Features
========

- **Pythonic**: friendly interface wrapped around simple functions.
- **Lightweight**: independent of any other prompt or visual libraries.
- **Adaptable**: works with any string formatting and window size.
- **Extensive**: packed with tweaks and features for any situation.

Installing
==========

.. code-block::

  pip3 install survey

Links
=====

- Greatly inspired by `AlecAivazis's GoLang <https://github.com/AlecAivazis/survey>`_ library.

Suggestions and contributions are greatly appreciated!
