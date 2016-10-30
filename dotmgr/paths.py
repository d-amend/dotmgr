# This file is part of dotmgr.
#
# dotmgr is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# dotmgr is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with dotmgr.  If not, see <http://www.gnu.org/licenses/>.
"""A module for dotfile repository management classes and service functions.
"""

from os import environ, makedirs
from os.path import expanduser, isdir, isfile


DEFAULT_DOTFILE_REPOSITORY_PATH = '~/.local/share/dotmgr/repository'
DEFAULT_DOTFILE_STAGE_PATH = '~/.local/share/dotmgr/stage'
DEFAULT_DOTFILE_TAG_CONFIG_PATH = '.config/dotmgr/tags.conf'

def prepare_dotfile_repository_path(verify, verbose):
    """Synthesizes the path to the dotfile repository.

    If DOTMGR_REPO is defined, it is read from the environment and returned.
    Otherwise the DEFAULT_DOTFILE_REPOSITORY_PATH is used.

    Args:
        verify:  If set to `True`, the program exits with an error message if the chosen path does
                 not point to a directory.
        verbose: If set to `True`, this function generates debug messages.

    Returns:
        The (absolute) path to the dotfile repository.
    """
    dotfile_repository_path = expanduser(DEFAULT_DOTFILE_REPOSITORY_PATH)
    if 'DOTMGR_REPO' in environ:
        dotfile_repository_path = environ['DOTMGR_REPO']

    if verify and not isdir(dotfile_repository_path):
        print('Error: dotfile repository {} does not exist'.format(dotfile_repository_path))
        exit()

    if verbose:
        print('Using dotfile repository at {}'.format(dotfile_repository_path))
    return dotfile_repository_path

def prepare_dotfile_stage_path(verbose):
    """Synthesizes the path to the dotfile stage directory.

    If DOTMGR_STAGE is defined, it is read from the environment and returned.
    Otherwise the DEFAULT_DOTFILE_STAGE_PATH is used.
    If the chosen directory does not exist, it is created automatically.

    Args:
        verbose: If set to `True`, this function generates debug messages.

    Returns:
        The (absolute) path to the dotfile stage directory.
    """
    dotfile_stage_path = expanduser(DEFAULT_DOTFILE_STAGE_PATH)
    if 'DOTMGR_STAGE' in environ:
        dotfile_stage_path = environ['DOTMGR_STAGE']

    if not isdir(dotfile_stage_path):
        if verbose:
            print('Preparing stage at {}'.format(dotfile_stage_path))
        makedirs(dotfile_stage_path)
    elif verbose:
        print('Using stage at {}'.format(dotfile_stage_path))
    return dotfile_stage_path

def prepare_tag_config_path(bootstrap, dotfile_repository_path, verify, verbose):
    """Synthesizes the path to the dotfile stage directory.

    If DOTMGR_TAG_CONF is defined, it is read from the environment and returned.
    Otherwise the DEFAULT_DOTFILE_STAGE_PATH is appended to the path of the user's home directory.
    If the chosen path does not point to a file, the program exits with an error message.

    Args:
        bootstrap: If `True`, a path to the config within in the dotfile repository is returned.
        dotfile_repository_path: The path to the dotfile repository (may be `None` if `boostrap` is
                                 not set).
        verify:  If set to `True`, the program exits with an error message if the chosen path does
                 not point to a file.
        verbose: If set to `True`, this function generates debug messages.

    Returns:
        The (absolute) path to the tag configuration file.
    """
    if bootstrap:
        dotfile_tag_config_path = dotfile_repository_path + '/' + DEFAULT_DOTFILE_TAG_CONFIG_PATH
    else:
        dotfile_tag_config_path = expanduser('~/' + DEFAULT_DOTFILE_TAG_CONFIG_PATH)
        if 'DOTMGR_TAG_CONF' in environ:
            dotfile_tag_config_path = environ['DOTMGR_TAG_CONF']

    if verify and not isfile(dotfile_tag_config_path):
        print('Error: Tag configuration file "{}" not found!\n'
              '       You can use -b to bootstrap it from your dotfile repository\n'
              '       or set $DOTMGR_TAG_CONF to override the default path.'\
              .format(dotfile_tag_config_path))
        exit()

    if verbose:
        print('Using dotfile tags config at {}'.format(dotfile_tag_config_path))
    return dotfile_tag_config_path
