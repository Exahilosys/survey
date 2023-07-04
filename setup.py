import setuptools

with open('README.rst') as file:
    readme = file.read()

author = 'Exahilosys'
project = 'survey'

url = 'https://github.com/{0}/{1}'.format(author, project)

setuptools.setup(
    name = project,
    python_requires = '>=3.7',
    use_scm_version = True,
    setup_requires = [
        'setuptools_scm'
    ],
    url = url,
    packages = setuptools.find_packages(),
    license = 'MIT',
    description = 'A simple library for creating beautiful interactive prompts.',
    long_description = readme,
    extras_require = {
        'docs': [
            'sphinx',
            'sphinx-rtd-theme',
            'sphinx-paramlinks',
            'sphinx-autodoc-typehints'
        ]
    }
)