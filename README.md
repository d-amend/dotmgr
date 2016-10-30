# What is `dotmgr`?
`dotmgr` is a little helper script you can use to manage and deploy your dotfiles across multiple
machines. The idea is to define tags for the different hosts, such as "laptop", "headless" or "work"
and filter dotfile templates containing configurations for all hosts based on those tags.

# Getting started
## Initial run
If you already have a repository containing your dotfiles, you can simply clone it:
```
dotmgr -I git@github.com:<user>/dotfiles.git
```

If the tag configuration is not found, `dotmgr` will automatically create one and commit it.
If you do not have a repository yet, you can let `dotmgr` create one for you:
```
dotmgr -I git@github.com:<user>/dotfiles.git
```

This will also generate and commit an initial tag configuration.

When the repository is set up, you can specialize and link all dotfiles in bootstrapping mode, which
reads the tag configuration from the repository instead of your home directory:
```
dotmgr -Sbl
```

On consecutive invocations of the script you can omit the `-b` flag, as the tag configuration is now
symlinked linked to your home directory. Please refer to the scripts `--help` option for more
information on command line options and arguments.

## Files and directories
### Tag configuration
The script relies on a simple configuration file that defines active tags for hostnames in the
following format:
```
hostnameA: tagA1 tagA2 ...
hostnameB: tagB1 tagB2 ...
```
This file is normally read from `.config/dotmgr/tags.conf` in your home directory. You can
override this default by setting the environment variable `$DOTMGR_TAG_CONF`.

You can (and should) also store the configuration in your dotfile repository. The script provides a
special command line option that allows you to read the tag configuration from your dotfile
repository the first time you run the script. Please see "Getting started" for details.

### Dotfile repository
Dotfile templates - also called "generic dotfiles" - are stored in a git repository. Each dotfile's
path relative to the repository's root directory is the same as relative to your home directory.

Special comments in the dotfiles are used to indicate blocks (tag-blocks) that should either be
commented out or left intact, depending on the tags activated for a host. Note that for this to
work, the first line of a dotfile **must** begin with a comment.

The dotfile repository path default is `~/.local/share/dotmgr/repository`. It can be modified using
the environment variable `$DOTMGR_REPO`.

### Stage directory
This directory contains the specific dotfiles for the current host, organized exactly as in your
home directory and the repository. During installation (specialization), dotmgr creates symlinks in
your home directory that point to the stage.

The default path is `~/.local/share/dotmgr/stage` and can be overriden with the environment
variable `$DOTMGR_STAGE`.

## Workflow
After you have changed a file, you can re-generalize it, for example:
```
dotmgr -G .vimrc
```
Omitting the file path (which has to be a path relative to your home directory) lets you generalize
all dotfiles one by one.

When files in the dotfile repository change, you can apply those changes to your "hot" dotfiles:
```
dotmgr -Sl
```
It is always best to pass the `-l` option along, in order to automatically link new dotfiles. If
you want to specialize only a single file, just add its path to the command line.

You can tell `dotmgr` about a new dotfile it should care about by issuing:
```
dotmgr -A <file>
```
To forget about a file, delete it from both the stage and the repository:
```
dotmgr -Dr <file>
```

## Git integration
The program can interact with the repository and automate or at least simplify some pretty
repetitive actions when managing dotfiles. There are options for
* initialization or cloning of remote repositories as shown in "Getting started",
* automatically committing changes to dotfiles,
* automatically synchronizing with a remote repository before specialization / after generalization.

In addition, theres an option that lets you execute git commands in the dotfile repository without
having to `cd` into it first. Please refer to `--help` for more information.

# Filtering
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

# Advanced vim magic
Adding the following line to your .vimrc automagically invokes the script each time you save a
dotfile in your home directory:
```
autocmd BufWritePost ~/.* !dotmgr -G %
```
