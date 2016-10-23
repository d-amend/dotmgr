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
from os.path import dirname, isdir, join
from socket import gethostname

from git import Repo
from git.cmd import Git
from git.exc import GitCommandError


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

    def _git(self):
        if not self._git_instance:
            self._git_instance = Repo(self.path).git
        return self._git_instance

    def clone(self, url):
        """Clones a dotfile repository.

        Args:
            url: The URL of the repository to clone.
        """
        print('Cloning {} into {}'.format(url, self.path))
        try:
            Git().clone(url, self.path)
        except GitCommandError as error:
            print(error.stderr)

    def execute(self, args):
        """Executes a git command in the dotfile repository.

        Args:
            args: Command line arguments for git.
        """
        args.insert(0, 'git')
        if self.verbose:
            print('Executing `{}`'.format(' '.join(args)))
        print(self._git().execute(args))

    def initialize(self, tag_config_path):
        """Initializes an empty git repository and creates an initial tag configuration.

        Args:
            tag_config_path: The (relative) path to the dotfile tag configuration.
        """
        print('Initializing empty repository in {}'.format(self.path))
        if isdir(self.path):
            print('Error: The target directory already exists.')
            exit()
        try:
            Git().init(self.path)
        except GitCommandError as error:
            print(error.stderr)

        print('Creating initial tag configuration')
        full_path = join(self.path, tag_config_path)
        makedirs(dirname(full_path))
        with open(full_path, 'w') as tag_config:
            tag_config.write('{0}: {0}'.format(gethostname()))

        print('Committing tag configuration')
        try:
            self._git().add(tag_config_path)
            self._git().commit(message='Add initial dotmgr tag configuration')
        except GitCommandError as error:
            print(error.stderr)

    def push(self):
        """Pushes to upstream.
        """
        print('Pushing to upstream')
        self._git().push()

    def pull(self):
        """Pulls from upstream.
        """
        print('Pulling from upstream')
        self._git().pull()

    def remove(self, dotfile_path):
        """Commits the removal of a dotfile.

        Args:
            dotfile_path: The relative path to the dotfile to remove.
        """
        print('Committing removal of {}'.format(dotfile_path))
        try:
            self._git().rm(dotfile_path, cached=True)
            self._git().commit(message='Remove {}'.format(dotfile_path))
        except GitCommandError as error:
            print(error.stderr)

    def update(self, dotfile_path):
        """Commits changes to a dotfile.

        Args:
            dotfile_path: The relative path to the dotfile to commit.
        """
        print('Committing changes to {}'.format(dotfile_path))
        try:
            self._git().add(dotfile_path)
            self._git().commit(message='Update {}'.format(dotfile_path))
        except GitCommandError as error:
            print(error.stderr)
