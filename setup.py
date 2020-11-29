import setuptools
import os

with open('README.rst') as file:
    readme = file.read()

name = 'survey'

github_version = os.getenv('GITHUB_VERSION')
github_version_parts = github_version.split('/')
version = github_version_parts[-1].lstrip('v')

author = 'Exahilosys'

url = f'https://github.com/{author}/{name}'

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
        'wrapio>=0.3.5'
    ],
    extras_require = {
        'docs': [
            'sphinx',
            'sphinx_rtd_theme'
        ]
    }
)
