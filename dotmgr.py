#!/usr/bin/python3
from argparse import ArgumentParser
from os import environ, listdir, makedirs, makedirs, remove, symlink
from os.path import dirname, exists, expanduser, isdir, islink
from shutil import move, rmtree
from socket import gethostname
from sys import exit

import re

DEBUG = True

default_dotfile_repository_path = '~/repositories/dotfiles'
default_dotfile_stage_path      = 'stage'
default_dotfile_tag_config_path = 'dotmgr.conf'
dotfile_repository_path = None
dotfile_stage_path      = None
dotfile_tag_config_path = None

parser = ArgumentParser(description='Generalize / specialize dotfiles',
                        epilog="""Required files and paths:
General dotfiles are read from / written to {}. You can set the environment variable $DOTMGR_REPO to change this.
The default stage directory is $DOTMGR_REPO/{}. This can be overridden with $DOTMGR_STAGE.
Tags are read from $DOTMGR_REPO/{}, which can be changed by setting $DOTMGR_TAG_CONF.
""".format(default_dotfile_repository_path, default_dotfile_stage_path, default_dotfile_tag_config_path))
parser.add_argument('-C', '--clean', action='store_true',
                    help='Remove all symlinks and clear the stage');
parser.add_argument('-G', '--generalize-all', action='store_true',
                    help='Generalize all dotfiles currently on stage');
parser.add_argument('-L', '--link-all', action='store_true',
                    help='Update all symlinks (use in conjunction with -S)');
parser.add_argument('-S', '--specialize-all', action='store_true',
                    help='Specialize all dotfiles in the repository');
parser.add_argument('-a', '--add', metavar='FILE',
                    help='Add a dotfile from the home directory');
parser.add_argument('-g', '--generalize', metavar='FILE',
                    help='Generalize a dotfile from the stage');
parser.add_argument('-l', '--link', action='store_true',
                    help='Place a symlink to a file on stage (use in conjunction with -s)');
parser.add_argument('-r', '--remove', metavar='FILE',
                    help='Remove a dotfile from the stage and delete its symlink');
parser.add_argument('-s', '--specialize', metavar='FILE',
                    help='Specialize a dotfile from the repository');

def cleanup(dotfile_name):
    print('Removing {} and its symlink'.format(dotfile_name))
    try:
        remove(home_path(dotfile_name))
    except FileNotFoundError:
        print('Symlink for {} not found'.format(dotfile_name))
    remove(stage_path(dotfile_name))

def cleanup_directory(directory_path):
    for entry in listdir(stage_path(directory_path)):
        full_path = directory_path + '/' + entry
        if isdir(full_path):
            cleanup_directory(full_path)
        else:
            cleanup(full_path)

def generalize(dotfile_path, tags):
    print('Generalizing ' + dotfile_path)
    specific_content = None
    with open(stage_path(dotfile_path)) as specific_dotfile:
        specific_content = specific_dotfile.readlines()

    makedirs(repo_path(dirname(dotfile_path)), exist_ok=True)
    with open(repo_path(dotfile_path), 'w') as generic_dotfile:
        for line in specific_content:
            # TODO
            generic_dotfile.write(line)

def generalize_directory(directory_path, tags):
    for entry in listdir(stage_path(directory_path)):
        if entry == '.git':
            continue
        full_path = directory_path + '/' + entry
        if isdir(full_path):
            generalize_directory(full_path, tags)
        else:
            generalize(full_path, tags)

def get_tags():
    hostname = gethostname()
    tag_config = None
    with open(dotfile_tag_config_path) as config:
        tag_config = config.readlines()

    for line in tag_config:
        if line.startswith(hostname + ':'):
            tags = line.split(':')[1]
            tags = tags.split()
            if DEBUG:
                print('Found tags: {}'.format(', '.join(tags)))
            return tags

def home_path(dotfile_name):
    return expanduser('~/{}'.format(dotfile_name))

def identify_comment_sequence(line):
    matches = re.findall(r'\S+', line)
    if not matches:
        print('Could not identify a comment character!')
        exit()
    seq = matches[0]
    if DEBUG:
        print('Identified comment character sequence: {}'.format(seq))
    return seq

def link(dotfile_path):
    link = home_path(dotfile_path)
    if exists(link):
        return

    dest = stage_path(dotfile_path)
    print("Creating symlink {} -> {}".format(link, dest))
    makedirs(dirname(link), exist_ok=True)
    symlink(dest, link)

def link_directory(path):
    for entry in listdir(stage_path(path)):
        full_path = path + '/' + entry
        if isdir(stage_path(full_path)):
            link_directory(full_path)
        else:
            link(full_path)

def repo_path(dotfile_name):
    return dotfile_repository_path + '/' + dotfile_name

def specialize(dotfile_path, tags):
    print('Specializing ' + dotfile_path)
    generic_content = None
    with open(repo_path(dotfile_path)) as generic_dotfile:
        generic_content = generic_dotfile.readlines()
    if not generic_content:
        return

    cseq = identify_comment_sequence(generic_content[0])

    makedirs(stage_path(dirname(dotfile_path)), exist_ok=True)
    with open(stage_path(dotfile_path), 'w') as specific_dotfile:
        comment_out = False
        for line in generic_content:
            if '{0}{0}only'.format(cseq) in line:
                section_tags = line.split()
                section_tags = section_tags[1:]
                if DEBUG:
                    print('Found section only for {}'.format(', '.join(section_tags)))
                if not [tag for tag in tags if tag in section_tags]:
                    specific_dotfile.write(line)
                    comment_out = True
                    continue
            if '{0}{0}not'.format(cseq) in line:
                section_tags = line.split()
                section_tags = section_tags[1:]
                if DEBUG:
                    print('Found section not for {}'.format(', '.join(section_tags)))
                if [tag for tag in tags if tag in section_tags]:
                    specific_dotfile.write(line)
                    comment_out = True
                    continue

            if '{0}{0}end'.format(cseq) in line:
                comment_out = False

            if comment_out:
                specific_dotfile.write(cseq + line)
            else:
                specific_dotfile.write(line)

def specialize_directory(directory_path, tags):
    for entry in listdir(repo_path(directory_path)):
        if entry == '.git':
            continue
        full_path = directory_path + '/' + entry
        if isdir(stage_path(full_path)):
            specialize_directory(full_path, tags)
        else:
            specialize(full_path, tags)

def stage_path(dotfile_name):
    return dotfile_stage_path + '/' + dotfile_name

def update_symlinks():
    for entry in listdir(dotfile_stage_path):
        if isdir(stage_path(entry)):
            link_directory(entry)
        else:
            link(entry)

if __name__ == "__main__":
    # Prepare dotfile repository path
    dotfile_repository_path = expanduser(default_dotfile_repository_path)
    if 'DOTMGR_REPO' in environ:
        dotfile_repository_path = environ['DOTMGR_REPO']
    if not exists(dotfile_repository_path):
        print('Error: dotfile repository {} does not exist'.format(dotfile_repository_path))
        exit()

    # Prepare dotfile stage path
    dotfile_stage_path = expanduser(default_dotfile_repository_path + '/' + default_dotfile_stage_path)
    if 'DOTMGR_STAGE' in environ:
        dotfile_stage_path = environ['DOTMGR_STAGE']
    if not exists(dotfile_stage_path):
        makedirs(dotfile_stage_path)

    # Prepare tag config path
    dotfile_tag_config_path = expanduser(default_dotfile_repository_path + '/' + default_dotfile_tag_config_path)
    if 'DOTMGR_TAG_CONF' in environ:
        dotfile_tag_config_path = environ['DOTMGR_TAG_CONF']

    # Parse arguments and execute selected action
    args = parser.parse_args()
    if args.clean:
        print('Cleaning')
        for entry in listdir(dotfile_stage_path):
            if isdir(dotfile_stage_path + '/' + entry):
                cleanup_directory(entry)
            else:
                cleanup(entry)
        rmtree(dotfile_stage_path)
        exit()
    if args.generalize_all:
        print('Generalizing all dotfiles');
        tags = get_tags()
        for entry in listdir(dotfile_stage_path):
            if isdir(dotfile_stage_path + '/' + entry):
                generalize_directory(entry, tags)
            else:
                generalize(entry, tags)
        exit()
    if args.specialize_all:
        print('Specializing all dotfiles');
        tags = get_tags()
        for entry in listdir(dotfile_repository_path):
            if isdir(dotfile_repository_path + '/' + entry):
                if repo_path(entry) == dotfile_stage_path \
                or entry == '.git':
                    continue
                specialize_directory(entry, tags)
            else:
                if repo_path(entry) == dotfile_tag_config_path:
                    continue
                specialize(entry, tags)
        if args.link_all:
            update_symlinks()
    if args.add:
        dotfile_name = args.add
        home = home_path(dotfile_name);
        if islink(home):
            exit()
        stage = stage_path(dotfile_name);
        print('Moving dotfile {} => {}'.format(home, stage))
        move(home, stage)
        link(dotfile_name)
        generalize(dotfile_name, get_tags())
        exit()
    if args.generalize:
        generalize(args.generalize, get_tags())
        exit()
    if args.remove:
        cleanup(args.remove)
        exit()
    if args.specialize:
        specialize(repo_path(args.specialize), get_tags())
        if args.link:
            link(args.specialize)
        exit()
