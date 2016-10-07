#!/usr/bin/env python3
"""A module for dotfile management classes and service functions.
"""

from os import listdir, makedirs, remove, symlink
from os.path import dirname, exists, expanduser, isdir
from re import findall
from socket import gethostname


class Manager(object):
    """An instance of this class can be used to manage dotfiles.

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
        self.tags = self.get_tags()

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

    def generalize(self, dotfile_path):
        """Generalizes a dotfile from the stage.

        Identifies and un-comments blocks deactivated for this host.
        The generalized file is written to the repository.

        Args:
            dotfile_path: The relative path to the dotfile to generalize.
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
                    if not [tag for tag in self.tags if tag in section_tags]:
                        generic_dotfile.write(line)
                        strip = True
                        continue
                    strip = False
                if '{0}{0}not'.format(cseq) in line:
                    section_tags = line.split()
                    section_tags = section_tags[1:]
                    if self.verbose:
                        print('Found section not for {}'.format(', '.join(section_tags)))
                    if [tag for tag in self.tags if tag in section_tags]:
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

    def generalize_directory(self, directory_path):
        """Recursively generalizes a directory of dotfiles on stage.

        Args:
            directory_path: The relative path to the directory to generalize.
        """
        for entry in listdir(self.stage_path(directory_path)):
            if entry == '.git':
                continue
            full_path = directory_path + '/' + entry
            if isdir(self.stage_path(full_path)):
                self.generalize_directory(full_path)
            else:
                self.generalize(full_path)

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
        matches = findall(r'\S+', line)
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

    def specialize(self, dotfile_path):
        """Specializes a dotfile from the repository.

        Identifies and comments out blocks not valid for this host.
        The specialized file is written to the stage directory.

        Args:
            dotfile_path: The relative path to the dotfile to specialize.
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
                    if not [tag for tag in self.tags if tag in section_tags]:
                        specific_dotfile.write(line)
                        comment_out = True
                        continue
                    comment_out = False
                if '{0}{0}not'.format(cseq) in line:
                    section_tags = line.split()
                    section_tags = section_tags[1:]
                    if self.verbose:
                        print('Found section not for {}'.format(', '.join(section_tags)))
                    if [tag for tag in self.tags if tag in section_tags]:
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

    def specialize_directory(self, directory_path):
        """Recursively specializes a directory of dotfiles from the repository.

        Args:
            directory_path: The relative path to the directory to specialize.
        """
        for entry in listdir(self.repo_path(directory_path)):
            if entry == '.git':
                continue
            full_path = directory_path + '/' + entry
            if isdir(self.repo_path(full_path)):
                self.specialize_directory(full_path)
            else:
                self.specialize(full_path)

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
