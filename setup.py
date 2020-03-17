# coding: utf8
from setuptools import setup, find_packages
from getsub.__version__ import __version__

with open("requirments.txt") as f:
    requirments = f.read().strip().splitlines()

setup(
    author="gyh1621",
    author_email="guoyh01@gmail.com",
    description="download subtitles easily",
    license="MIT",
    name="getsub",
    version=__version__,
    packages=find_packages(),
    install_requires=requirments,
    include_package_data=True,
    entry_points={"console_scripts": ["getsub = getsub.main: main"]},
    zip_safe=False,
    long_description=__doc__,
)
