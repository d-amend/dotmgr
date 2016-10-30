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

from os import makedirs
from os.path import dirname, isdir, isfile, join
from socket import gethostname

from git import Repo
from git.cmd import Git
from git.exc import GitCommandError, InvalidGitRepositoryError


class Repository(object):
    """An instance of this class can be used to manage dotfiles.

    Attributes:
        path:    The absolute path to the dotfile repository.
        verbose: If set to `True`, debug messages are generated.
    """

    def __init__(self, repository_path, verbose):
        self.path = repository_path
        self.verbose = verbose
        self._git_instance = None

    def _commit_file(self, dotfile_path, message):
        """Commit helper function.

        Args:
            dotfile_path: The relative path to the dotfile to commit.
            message:      A commit message.
        """
        print('Committing {}'.format(dotfile_path))
        _exec_fancy(lambda: self._git().stage(dotfile_path))
        _exec_fancy(lambda: self._git().commit(message=message))

    def _git(self):
        """Singleton factory for the Git object.
        """
        if not self._git_instance:
            try:
                self._git_instance = Repo(self.path).git
            except InvalidGitRepositoryError:
                print('Error: {} is not a git repository!\n'
                      '       You can try running `dotmgr -I` to initialize it.'.format(self.path))
                exit()
        return self._git_instance

    def add(self, dotfile_path):
        """Adds and commits a new dotfile.

        Args:
            dotfile_path: The relative path to the dotfile to commit.
        """
        self._commit_file(dotfile_path, 'Add {}'.format(dotfile_path))

    def clone(self, url):
        """Clones a dotfile repository.

        Args:
            url: The URL of the repository to clone.
        """
        print('Cloning {} into {}'.format(url, self.path))
        _exec_raw(lambda: Git().clone(url, self.path))

    def execute(self, args):
        """Executes a git command in the dotfile repository.

        Args:
            args: Command line arguments for git.
        """
        args.insert(0, 'git')
        if self.verbose:
            print('Executing `{}`'.format(' '.join(args)))
        _exec_raw(lambda: self._git().execute(args))

    def initialize(self, tag_config_path):
        """Initializes an empty git repository and creates and commits an initial tag configuration.

        If the repository already exists, only the tag configuration file is created and committed.

        Args:
            tag_config_path: The (relative) path to the dotfile tag configuration.
        """
        if not isdir(self.path):
            print('Initializing empty repository in {}'.format(self.path))
            _exec_raw(lambda: Git().init(self.path))

        try:
            self._git().rev_parse()
        except InvalidGitRepositoryError:
            print('Initializing repository in existing directory {}'.format(self.path))
            _exec_raw(lambda: Git(self.path).init())

        full_path = join(self.path, tag_config_path)
        if not isfile(full_path):
            print('Creating initial tag configuration')
            makedirs(dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as tag_config:
                tag_config.write('{0}: {0}'.format(gethostname()))
            self.add(tag_config_path)

    def push(self):
        """Pushes to upstream.
        """
        print('Pushing to upstream')
        _exec_fancy(lambda: self._git().push())

    def pull(self):
        """Pulls from upstream.
        """
        print('Pulling from upstream')
        _exec_fancy(lambda: self._git().pull())

    def remove(self, dotfile_path):
        """Commits the removal of a dotfile.

        Args:
            dotfile_path: The relative path to the dotfile to remove.
        """
        print('Committing removal of {}'.format(dotfile_path))
        _exec_fancy(lambda: self._git().rm(dotfile_path, cached=True))
        _exec_fancy(lambda: self._git().commit(message='Remove {}'.format(dotfile_path)))

    def update(self, dotfile_path, message=None):
        """Commits changes to a dotfile.

        Args:
            dotfile_path: The relative path to the dotfile to commit.
            message:      A commit message. If omitted, a default message is generated.
        """
        # Skip if the file has not changed
        if not self._git().diff(dotfile_path, name_only=True):
            return

        if not message:
            message = 'Update {}'.format(dotfile_path)
        self._commit_file(dotfile_path, message)

def _exec_fancy(func):
    """Executes a git command and handles errors gracefully.

    In case of errors a note on what failed and how to re-try the operation is printed and program
    execution is aborted.

    Args:
        func:          A function that executes a git command.
    """
    try:
        func()
    except GitCommandError as err:
        cmdline = ' '.join(err.command)
        args = ' '.join(err.command[1:])
        print('Error: Sorry, something went wrong during execution of `{}`. :-(\n'
              '       You can execute `dotmgr -V {}` to try again and find out what happened.'
              .format(cmdline, args))
        exit()

def _exec_raw(func):
    """Executes a git command.

    In case of errors the STDERR output of the command is printed and program execution is aborted.

    Args:
        func:          A function that executes a git command.
    """
    try:
        func()
    except GitCommandError as err:
        cmdline = ' '.join(err.command)
        print('Error: Execution of the command\n'
              '       {}\n'
              '       failed with the following message:'.format(cmdline))
        # Forward stderr from git
        print(err.args[2].decode('utf-8'))
        exit()
