
from setuptools import setup

setup(name='nicelogcat',
    python_requires='>3.7',
    version='0.0.1',
    description='vlog',
    url='git@github.com:cvlvxi/nicelogcat.git',
    author='0x5f3759df',
    author_email='bleh@bleh.com',
    license='',
    packages=['nicelogcat'],
    entry_points = {
    'console_scripts': ['nicelogcat = vlog:main']
    },
    zip_safe=False)