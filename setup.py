import setuptools

with open('README.md') as file:
    readme = file.read()

name = 'survey'

version = '2.0.4'

author = 'Exahilosys'

url = f'https://github.com/{author}/{name}'

setuptools.setup(
    name = name,
    version = version,
    url = url,
    packages = setuptools.find_packages(),
    license = 'MIT',
    description = 'A simple library for creating beautiful interactive prompts.',
    long_description = readme,
    long_description_content_type= 'text/markdown',
    install_requires = [
        'wrapio'
    ],
    extras_require = {
        'docs': [
            'sphinx',
            'sphinx_rtd_theme'
        ]
    }
)
