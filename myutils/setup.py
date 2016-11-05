try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'My Utils',
    'author': 'Florin Rosca',
    'url': 'URL to get it at.',
    'download_url': 'https://github.com/florin-rosca-us/playground-python/tree/master/myutils',
    'author_email': '',
    'version': '1.0',
    'install_requires': ['magic', 'wand'],
    'packages': ['myutils'],
    'scripts': [],
    'name': 'myutils'
}

setup(**config)