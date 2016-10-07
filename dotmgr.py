#!/usr/bin/env python3
"""Dotfile manager

A small script that can help you maintain your dotfiles across several devices.
"""

from argparse import ArgumentParser
from os import environ, listdir, makedirs
from os.path import exists, expanduser, isdir, isfile, islink
from shutil import move, rmtree
from manager import Manager, home_path


DEFAULT_DOTFILE_REPOSITORY_PATH = '~/repositories/dotfiles'
DEFAULT_DOTFILE_STAGE_PATH = '~/.local/share/dotmgr/stage'
DEFAULT_DOTFILE_TAG_CONFIG_PATH = '.config/dotmgr/tags.conf'


def main():
    """Program entry point.

    Where things start to happen...
    """
    # Check and parse arguments
    parser = ArgumentParser(description='Generalize / specialize dotfiles',
                            epilog="""Required files and paths:
    General dotfiles are read from / written to {}. You can set the environment variable $DOTMGR_REPO to change this.
    The default stage directory is {}. This can be overridden with $DOTMGR_STAGE.
    Tags are read from $HOME/{}, which can be changed by setting $DOTMGR_TAG_CONF.
    """.format(DEFAULT_DOTFILE_REPOSITORY_PATH, DEFAULT_DOTFILE_STAGE_PATH, DEFAULT_DOTFILE_TAG_CONFIG_PATH))
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
    args = parser.parse_args()

    # Enable verbose mode if requested
    verbose = False
    if args.verbose:
        verbose = True

    # Prepare dotfile repository path
    dotfile_repository_path = expanduser(DEFAULT_DOTFILE_REPOSITORY_PATH)
    if 'DOTMGR_REPO' in environ:
        dotfile_repository_path = environ['DOTMGR_REPO']
    if not exists(dotfile_repository_path):
        print('Error: dotfile repository {} does not exist'.format(dotfile_repository_path))
        exit()
    if verbose:
        print('Using dotfile repository at {}'.format(dotfile_repository_path))

    # Prepare dotfile stage path
    dotfile_stage_path = expanduser(DEFAULT_DOTFILE_STAGE_PATH)
    if 'DOTMGR_STAGE' in environ:
        dotfile_stage_path = environ['DOTMGR_STAGE']
    if not exists(dotfile_stage_path):
        makedirs(dotfile_stage_path)
    if verbose:
        print('Using stage at {}'.format(dotfile_stage_path))

    # Prepare tag config path and check if it exists
    if args.bootstrap:
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

    manager = Manager(dotfile_repository_path, dotfile_stage_path, dotfile_tag_config_path, verbose)

    # Execute selected action
    if args.clean:
        print('Cleaning')
        for entry in listdir(dotfile_stage_path):
            if isdir(dotfile_stage_path + '/' + entry):
                manager.cleanup_directory(entry)
            else:
                manager.cleanup(entry)
        rmtree(dotfile_stage_path)
        exit()
    if args.generalize_all:
        print('Generalizing all dotfiles')
        tags = manager.get_tags()
        for entry in listdir(dotfile_stage_path):
            if isdir(dotfile_stage_path + '/' + entry):
                manager.generalize_directory(entry, tags)
            else:
                manager.generalize(entry, tags)
        exit()
    if args.specialize_all:
        print('Specializing all dotfiles')
        tags = manager.get_tags()
        for entry in listdir(dotfile_repository_path):
            if isdir(dotfile_repository_path + '/' + entry):
                if manager.repo_path(entry) == dotfile_stage_path \
                or entry == '.git':
                    continue
                manager.specialize_directory(entry, tags)
            else:
                if manager.repo_path(entry) == dotfile_tag_config_path:
                    continue
                manager.specialize(entry, tags)
        if args.link_all:
            manager.update_symlinks()
        exit()
    if args.add:
        dotfile_name = args.add
        home = home_path(dotfile_name)
        if islink(home):
            exit()
        stage = manager.stage_path(dotfile_name)
        print('Moving dotfile   {} => {}'.format(home, stage))
        move(home, stage)
        manager.link(dotfile_name)
        manager.generalize(dotfile_name, manager.get_tags())
        exit()
    if args.generalize:
        manager.generalize(args.generalize, manager.get_tags())
        exit()
    if args.remove:
        manager.cleanup(args.remove)
        exit()
    if args.specialize:
        manager.specialize(manager.repo_path(args.specialize), manager.get_tags())
        if args.link:
            manager.link(args.specialize)
        exit()
    parser.print_help()

if __name__ == "__main__":
    main()
