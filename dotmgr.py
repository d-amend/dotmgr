#!/usr/bin/env python3
#
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
"""Dotfile manager

A small script that can help you maintain your dotfiles across several devices.
"""

from argparse import ArgumentParser
from os import environ, makedirs
from os.path import exists, expanduser, isfile
from app.manager import Manager


DEFAULT_DOTFILE_REPOSITORY_PATH = '~/repositories/dotfiles'
DEFAULT_DOTFILE_STAGE_PATH = '~/.local/share/dotmgr/stage'
DEFAULT_DOTFILE_TAG_CONFIG_PATH = '.config/dotmgr/tags.conf'


def prepare_argument_parser():
    """Creates and configures the argument parser for the CLI.
    """

    parser = ArgumentParser(description='Generalize / specialize dotfiles',
                            epilog="""Required files and paths:
    General dotfiles are read from / written to {}. You can set the environment variable $DOTMGR_REPO to change this.
    The default stage directory is {}. This can be overridden with $DOTMGR_STAGE.
    Tags are read from $HOME/{}, which can be changed by setting $DOTMGR_TAG_CONF.
    """.format(DEFAULT_DOTFILE_REPOSITORY_PATH,
               DEFAULT_DOTFILE_STAGE_PATH,
               DEFAULT_DOTFILE_TAG_CONFIG_PATH))
    parser.add_argument('-C', '--clean', action='store_true',
                        help='Remove all symlinks and clear the stage')
    parser.add_argument('-G', '--generalize-all', action='store_true',
                        help='Generalize all dotfiles currently on stage')
    parser.add_argument('-L', '--link-all', action='store_true',
                        help='Update all symlinks (use in conjunction with -S)')
    parser.add_argument('-S', '--specialize-all', action='store_true',
                        help='Specialize all dotfiles in the repository')
    parser.add_argument('-a', '--add', metavar='FILE',
                        help='Add a dotfile from the home directory')
    parser.add_argument('-b', '--bootstrap', action='store_true',
                        help='Read the tag configuration from the repository instead of $HOME')
    parser.add_argument('-g', '--generalize', metavar='FILE',
                        help='Generalize a dotfile from the stage')
    parser.add_argument('-l', '--link', action='store_true',
                        help='Place a symlink to a file on stage (use in conjunction with -s)')
    parser.add_argument('-r', '--remove', metavar='FILE',
                        help='Remove a dotfile from the stage and delete its symlink')
    parser.add_argument('-s', '--specialize', metavar='FILE',
                        help='Specialize a dotfile from the repository')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (useful for debugging)')
    return parser

def prepare_dotfile_repository_path(verbose):
    """Synthesizes the path to the dotfile repository.

    If DOTMGR_REPO is defined, it is read from the environment and returned.
    Otherwise the DEFAULT_DOTFILE_REPOSITORY_PATH is used.
    If the chosen path does not point to a directory, the program exits with an error message.

    Args:
        verbose: If set to `True`, this function generates debug messages.

    Returns:
        The (absolute) path to the dotfile repository.
    """

    dotfile_repository_path = expanduser(DEFAULT_DOTFILE_REPOSITORY_PATH)
    if 'DOTMGR_REPO' in environ:
        dotfile_repository_path = environ['DOTMGR_REPO']

    if not exists(dotfile_repository_path):
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

    if not exists(dotfile_stage_path):
        if verbose:
            print('Preparing stage at {}'.format(dotfile_stage_path))
        makedirs(dotfile_stage_path)
    elif verbose:
        print('Using stage at {}'.format(dotfile_stage_path))
    return dotfile_stage_path

def prepare_tag_config_path(bootstrap, dotfile_repository_path, verbose):
    """Synthesizes the path to the dotfile stage directory.

    If DOTMGR_TAG_CONF is defined, it is read from the environment and returned.
    Otherwise the DEFAULT_DOTFILE_STAGE_PATH is appended to the path of the user's home directory.
    If the chosen path does not point to a file, the program exits with an error message.

    Args:
        bootstrap: If `True`, a path to the config within in the dotfile repository is returned.
        dotfile_repository_path: The path to the dotfile repository (may be `None` if `boostrap` is
                                 not set).
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

    if not isfile(dotfile_tag_config_path):
        print('Error: Tag configuration file "{}" not found!\n'
              '       You can use -b to bootstrap it from your dotfile repository\n'
              '       or set $DOTMGR_TAG_CONF to override the default path.'\
              .format(dotfile_tag_config_path))
        exit()
    if verbose:
        print('Using dotfile tags config at {}'.format(dotfile_tag_config_path))
    return dotfile_tag_config_path

def main():
    """Program entry point.

    Where things start to happen...
    """

    # Check and parse arguments
    parser = prepare_argument_parser()
    args = parser.parse_args()

    # Enable verbose mode if requested
    verbose = False
    if args.verbose:
        verbose = True

    # Prepare paths and dotfile manager
    dotfile_repository_path = prepare_dotfile_repository_path(verbose)
    dotfile_stage_path = prepare_dotfile_stage_path(verbose)
    dotfile_tag_config_path = prepare_tag_config_path(args.bootstrap,
                                                      dotfile_repository_path,
                                                      verbose)
    manager = Manager(dotfile_repository_path, dotfile_stage_path, dotfile_tag_config_path, verbose)

    # Execute selected action
    if args.clean:
        manager.cleanup_all()
        exit()
    if args.generalize_all:
        manager.generalize_all()
        exit()
    if args.specialize_all:
        manager.specialize_all(args.link_all)
        exit()
    if args.add:
        manager.add(args.add)
        exit()
    if args.generalize:
        manager.generalize(args.generalize)
        exit()
    if args.remove:
        manager.cleanup(args.remove)
        exit()
    if args.specialize:
        manager.specialize(manager.repo_path(args.specialize))
        if args.link:
            manager.link(args.specialize)
        exit()
    parser.print_help()

if __name__ == "__main__":
    main()
