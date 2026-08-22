from setuptools import find_packages
from setuptools import setup

setup(
    name='interfaces_pkg',
    version='0.0.1',
    packages=find_packages(
        include=('interfaces_pkg', 'interfaces_pkg.*')),
)
