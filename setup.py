from distutils.core import setup
from setuptools import find_packages
from git.cmd import Git

setup(
    name='dotmgr',
    description='A small script that can help you maintain your dotfiles across several devices',
    keywords=['dotmgr', 'dotfile', 'management'],
    author='Sebastian Neuser',
    author_email='haggl@sineband.de',
    url='https://github.com/haggl/dotmgr',
    license='GPLv3+',
    version=Git().describe(tags=True, dirty=True, always=True),
    packages=find_packages(),
    scripts=['dotmgr/dotmgr'],
    install_requires=['gitpython']
)
