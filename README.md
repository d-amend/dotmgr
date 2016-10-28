# Dotfile Manager
A tag-based dotfile manager for multiple machines written in Python3.

## Dotfile repository
The generic dotfiles are stored in an external repository. Comments are used to indicate blocks
(tag-blocks) that should be commented out or used (uncommented) when a certain tag is active.
Note that for this to work, the first line of a dotfile must begin with a comment.

The dotfile repository path default is `~/.local/share/dotmgr/repository`. It can be modified using
the environment variable `$DOTMGR_REPO`.

## Tag configuration
The script relies on a simple configuration file that defines active tags for hostnames in the
following format:
```
hostnameA: tagA1 tagA2 ...
hostnameB: tagB1 tagB2 ...
```
This file is normally read from `.config/dotmgr/tags.conf` in your home directory. You can
override this default by setting the environment variable `$DOTMGR_TAG_CONF`.

You can (and should) also store the file in your dotfile repository. The script provides a special
command line option that allows you to read the tag configuration from your dotfile repository the
first time you run the script. Please see "Getting started" below for details.

## Tag-blocks
Create tag-blocks using a double comment sequence and the keyword `only` or `not`. A double comment
sequence followed by `end` ends a tag-block:
```
##only tagA tagB
# ordinary comment
echo Hello dotmgr
##end

##not tagC
echo Non-tagC hosts only
##end
```

Tag-blocks can also be written in an if-else kind of style:
```
##only tagA
echo Hello dotmgr
##not tagB
echo Cheers dotmgr
##end
```

## Stage directory
This directory contains the specific dotfiles for the current host. During installation
(specialization), dotmgr creates symlinks in the system ($HOME, /etc/(not yet)) that point to the
stage.

The default path is `~/.local/share/dotmgr/stage` and can be overriden with the environment
variable `$DOTMGR_STAGE`.

## Dotfile specialization
This is the workflow for generating specific dotfiles for the current hostname and installing them
in the system:

1. Read the tags activated for this hostname from the tag configuration
2. Create specific dotfiles by (un)commenting tag-blocks
3. Write them to the stage directory
4. (optional) Create symlinks

## Dotfile generalization
The generalized dotfile representation resides in the dotfile repository. Here, all tag-blocks are
uncommented to allow editing using syntax highlighting.

You can create generic dotfiles from dotfiles currently on stage. This process, reverses the changes
of the specialization and removes all comments from tag-blocks.

You can also directly add a file from the system, in which case the following steps are performed:

1. Move the file to the stage
2. Create a symlink to the file on stage
3. Generalize the file
4. Write it to the dotfile repository

## Getting started
Clone your dotfile repository:
```
mkdir -p ~/repositories
cd ~/repositories
git clone git@github.com:<user>/dotfiles.git
```

Create a tag.conf:
```
cd ~/repositories/dotfiles
mkdir -p .config/dotmgr
vim .config/dotmgr/tags.conf
```

Specialize and link all dotfiles in bootstrapping mode:
```
dotmgr -blS
```

On consecutive invocations of the script you can omit the `-b` flag, as the tag configuration is now
symlinked linked to your home directory. Please refer to the scripts `--help` option for more
information on command line options and arguments.

## Advanced vim magic
Adding the following line to your .vimrc automagically invokes the script each time you save a file
in your home directory:
```
autocmd BufWritePost ~/.* !dotmgr -G %
```
