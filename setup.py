from distutils.core import setup
from setuptools import find_packages
setup(
    name='dotmgr',
    description='A small script that can help you maintain your dotfiles across several devices',
    keywords=['dotmgr', 'dotfile', 'management'],
    author='Sebastian Neuser',
    author_email='haggl@sineband.de',
    url='https://github.com/haggl/dotmgr',
    license='GPLv3+',
    scripts=['dotmgr.py'],
    packages=find_packages(),
    version='0.1.0'
)
