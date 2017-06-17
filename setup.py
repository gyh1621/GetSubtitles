# coding: utf8
from setuptools import setup
from __init__ import __version__

setup(
    author="gyh1621",
    author_email="guoyh01@gmail.com",
    description="download subtitles easily",
    license="MIT",
    name='getsub',
    version=__version__,
    packages=[''],
    install_requires=[    # 依赖列表
        'requests>=2.9, <2.10',
        'bs4>=0.0.1',
        'guessit>=2.1, <2.2',
        'rarfile>=3.0'
    ],
    entry_points={
        'console_scripts': [
            'getsub = main: main'
        ]
    },
    zip_safe=False,
    long_description=__doc__
)
