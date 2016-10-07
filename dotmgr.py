#!/usr/bin/env python3
"""Dotfile manager

A small script that can help you maintain your dotfiles across several devices.
"""

from argparse import ArgumentParser
from os import environ, listdir, makedirs, remove, symlink
from os.path import dirname, exists, expanduser, isdir, isfile, islink
from shutil import move, rmtree
from socket import gethostname

import re

DEFAULT_DOTFILE_REPOSITORY_PATH = '~/repositories/dotfiles'
DEFAULT_DOTFILE_STAGE_PATH = '~/.local/share/dotmgr/stage'
DEFAULT_DOTFILE_TAG_CONFIG_PATH = '.config/dotmgr/tags.conf'

class Manager(object):
    """An instance of this class can be used to generalize or specialize dotfiles.

    Attributes:
        dotfile_repository_path: The absolute path to the dotfile repository.
        dotfile_stage_path: The absolute path to the dotfile stage directory.
        dotfile_tag_config_path: The absolute path to the dotfile tag configuration file.
        verbose: If set to `True`, debug messages are generated.
    """

    def __init__(self, dotfile_repository_path, dotfile_stage_path, dotfile_tag_config_path, verbose):
        self.dotfile_repository_path = dotfile_repository_path
        self.dotfile_stage_path = dotfile_stage_path
        self.dotfile_tag_config_path = dotfile_tag_config_path
        self.verbose = verbose

    def cleanup(self, dotfile_path):
        """Removes a dotfile from the stage and the symlink from $HOME.

        Args:
            dotfile_path: The relative path to the dotfile to remove.
        """
        print('Removing {} and its symlink'.format(dotfile_path))
        try:
            remove(home_path(dotfile_path))
        except FileNotFoundError:
            print('Warning: Symlink for {} not found'.format(dotfile_path))
        try:
            remove(self.stage_path(dotfile_path))
        except FileNotFoundError:
            print('Warning: {} is not on stage'.format(dotfile_path))

    def cleanup_directory(self, directory_path):
        """Recursively removes dotfiles from the stage and their symlinks from $HOME.

        Args:
            directory_path: The relative path to the directory to clean.
        """
        for entry in listdir(self.stage_path(directory_path)):
            full_path = directory_path + '/' + entry
            if isdir(self.stage_path(full_path)):
                self.cleanup_directory(full_path)
            else:
                self.cleanup(full_path)

    def generalize(self, dotfile_path, tags):
        """Generalizes a dotfile from the stage.

        Identifies and un-comments blocks deactivated for this host.
        The generalized file is written to the repository.

        Args:
            dotfile_path: The relative path to the dotfile to generalize.
            tags:         The tags for this host.
        """
        print('Generalizing ' + dotfile_path)
        specific_content = None
        try:
            with open(self.stage_path(dotfile_path)) as specific_dotfile:
                specific_content = specific_dotfile.readlines()
        except FileNotFoundError:
            print('It seems {0} is not handled by dotmgr.\n'
                  'You can add it with `{1} -a {0}`.'.format(dotfile_path, __file__))
        if not specific_content:
            return

        makedirs(self.repo_path(dirname(dotfile_path)), exist_ok=True)
        cseq = self.identify_comment_sequence(specific_content[0])

        makedirs(self.stage_path(dirname(dotfile_path)), exist_ok=True)
        with open(self.repo_path(dotfile_path), 'w') as generic_dotfile:
            strip = False
            for line in specific_content:
                if '{0}{0}only'.format(cseq) in line:
                    section_tags = line.split()
                    section_tags = section_tags[1:]
                    if self.verbose:
                        print('Found section only for {}'.format(', '.join(section_tags)))
                    if not [tag for tag in tags if tag in section_tags]:
                        generic_dotfile.write(line)
                        strip = True
                        continue
                    strip = False
                if '{0}{0}not'.format(cseq) in line:
                    section_tags = line.split()
                    section_tags = section_tags[1:]
                    if self.verbose:
                        print('Found section not for {}'.format(', '.join(section_tags)))
                    if [tag for tag in tags if tag in section_tags]:
                        generic_dotfile.write(line)
                        strip = True
                        continue
                    strip = False

                if '{0}{0}end'.format(cseq) in line:
                    strip = False

                if strip:
                    slices = line.split(cseq)
                    generic_dotfile.write(cseq.join(slices[1:]))
                else:
                    generic_dotfile.write(line)

    def generalize_directory(self, directory_path, tags):
        """Recursively generalizes a directory of dotfiles on stage.

        Args:
            directory_path: The relative path to the directory to generalize.
            tags:           The tags for this host.
        """
        for entry in listdir(self.stage_path(directory_path)):
            if entry == '.git':
                continue
            full_path = directory_path + '/' + entry
            if isdir(self.stage_path(full_path)):
                self.generalize_directory(full_path, tags)
            else:
                self.generalize(full_path, tags)

    def get_tags(self):
        """Parses the dotmgr config file and extracts the tags for the current host.

        Reads the hostname and searches the dotmgr config for a line defining tags for the host.

        Returns:
            The tags defined for the current host.
        """
        hostname = gethostname()
        tag_config = None
        with open(self.dotfile_tag_config_path) as config:
            tag_config = config.readlines()

        for line in tag_config:
            if line.startswith(hostname + ':'):
                tags = line.split(':')[1]
                tags = tags.split()
                if self.verbose:
                    print('Found tags: {}'.format(', '.join(tags)))
                return tags
        print('Warning: No tags found for this machine!')
        return [""]

    def identify_comment_sequence(self, line):
        """Parses a line and extracts the comment character sequence.

        Args:
            line: A commented (!) line from the config file.

        Returns:
            The characters used to start a comment line.
        """
        matches = re.findall(r'\S+', line)
        if not matches:
            print('Could not identify a comment character!')
            exit()
        seq = matches[0]
        if self.verbose:
            print('Identified comment character sequence: {}'.format(seq))
        return seq

    def link(self, dotfile_path):
        """Links a dotfile from the stage to $HOME.

        Args:
            dotfile_path: The relative path to the dotfile to link.
        """
        link_path = home_path(dotfile_path)
        if exists(link_path):
            return

        dest_path = self.stage_path(dotfile_path)
        print("Creating symlink {} -> {}".format(link_path, dest_path))
        makedirs(dirname(link_path), exist_ok=True)
        symlink(dest_path, link_path)

    def link_directory(self, directory_path):
        """Recursively links a directory of dotfiles from the stage to $HOME.

        Args:
            directory_path: The relative path to the directory to link.
        """
        for entry in listdir(self.stage_path(directory_path)):
            full_path = directory_path + '/' + entry
            if isdir(self.stage_path(full_path)):
                self.link_directory(full_path)
            else:
                self.link(full_path)

    def repo_path(self, dotfile_name):
        """Returns the absolute path to a named dotfile in the repository.

        Args:
            dotfile_name: The name of the dotfile whose path should by synthesized.

        Returns:
            The absolute path to the dotfile in the repository.
        """
        return self.dotfile_repository_path + '/' + dotfile_name

    def specialize(self, dotfile_path, tags):
        """Specializes a dotfile from the repository.

        Identifies and comments out blocks not valid for this host.
        The specialized file is written to the stage directory.

        Args:
            dotfile_path: The relative path to the dotfile to specialize.
            tags:         The tags for this host.
        """
        print('Specializing ' + dotfile_path)
        generic_content = None
        with open(self.repo_path(dotfile_path)) as generic_dotfile:
            generic_content = generic_dotfile.readlines()
        if not generic_content:
            return

        cseq = self.identify_comment_sequence(generic_content[0])

        makedirs(self.stage_path(dirname(dotfile_path)), exist_ok=True)
        with open(self.stage_path(dotfile_path), 'w') as specific_dotfile:
            comment_out = False
            for line in generic_content:
                if '{0}{0}only'.format(cseq) in line:
                    section_tags = line.split()
                    section_tags = section_tags[1:]
                    if self.verbose:
                        print('Found section only for {}'.format(', '.join(section_tags)))
                    if not [tag for tag in tags if tag in section_tags]:
                        specific_dotfile.write(line)
                        comment_out = True
                        continue
                    comment_out = False
                if '{0}{0}not'.format(cseq) in line:
                    section_tags = line.split()
                    section_tags = section_tags[1:]
                    if self.verbose:
                        print('Found section not for {}'.format(', '.join(section_tags)))
                    if [tag for tag in tags if tag in section_tags]:
                        specific_dotfile.write(line)
                        comment_out = True
                        continue
                    comment_out = False

                if '{0}{0}end'.format(cseq) in line:
                    comment_out = False

                if comment_out:
                    specific_dotfile.write(cseq + line)
                else:
                    specific_dotfile.write(line)

    def specialize_directory(self, directory_path, tags):
        """Recursively specializes a directory of dotfiles from the repository.

        Args:
            directory_path: The relative path to the directory to specialize.
            tags:           The tags for this host.
        """
        for entry in listdir(self.repo_path(directory_path)):
            if entry == '.git':
                continue
            full_path = directory_path + '/' + entry
            if isdir(self.repo_path(full_path)):
                self.specialize_directory(full_path, tags)
            else:
                self.specialize(full_path, tags)

    def stage_path(self, dotfile_name):
        """Returns the absolute path to a named dotfile on stage.

        Args:
            dotfile_name: The name of the dotfile whose path should by synthesized.

        Returns:
            The absolute stage path to the dotfile.
        """
        return self.dotfile_stage_path + '/' + dotfile_name

    def update_symlinks(self):
        """Creates missing symlinks to all dotfiles on stage.

        Also automagically creates missing folders in $HOME.
        """
        for entry in listdir(self.dotfile_stage_path):
            if isdir(self.stage_path(entry)):
                self.link_directory(entry)
            else:
                self.link(entry)

def home_path(dotfile_name):
    """Returns the absolute path to a named dotfile in the user's $HOME directory.

    Args:
        dotfile_name: The name of the dotfile whose path should by synthesized.

    Returns:
        The absolute path to the dotfile in the user's $HOME directory.
    """
    return expanduser('~/{}'.format(dotfile_name))

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
