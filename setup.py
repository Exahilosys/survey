import setuptools

with open('README.rst') as file:
    readme = file.read()

name = 'survey'

version = '3.4.2'

author = 'Exahilosys'

url = 'https://github.com/{0}/{1}'.format(author, name)

setuptools.setup(
    name = name,
    python_requires = '>=3.5',
    version = version,
    url = url,
    packages = setuptools.find_packages(),
    license = 'MIT',
    description = 'A simple library for creating beautiful interactive prompts.',
    long_description = readme,
    install_requires = [
        'wrapio>=1.0.0'
    ],
    extras_require = {
        'docs': [
            'sphinx',
            'sphinx_rtd_theme'
        ]
    }
)
