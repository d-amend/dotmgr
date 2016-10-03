# Dotfile Manager
Tag-based dotfile manager for multiple machines written in Python3.

## Dotfile repository
The generic dotfiles are stored in an external repository. Comments are used to indicate blocks (tag-blocks) that should be commented out or used (uncommented) when a certain tag is active. Note that dotfiles must begin with a comment.

This repository also contains the config file dotmgr.conf which has a list of tags for each hostname:

```
hostnameA: tagA1 tagA2 ...
hostnameB: tagB1 tagB2 ...
```

The dotfile repository path default is `~/repositories/dotfiles`. It can be modified using the envar `$DOTMGR_REPO`

## Tag-blocks
Using double-comments and the keywords `only` and `not` tag-blocks are created:
```
## only tagA tagB
# ordinary comment
echo Hello dotmgr
## end

## not tagC
echo Non-tagC hosts only
## end
```

Tag-blocks can also be used in an if-else kind of style:
```
## only tagA
echo Hello dotmgr
## not tagB
echo Cheers dotmgr
## end
```

## Stage directory
This directory contains the specific dotfiles for the current host. During installation (specialization), dotmgr creates symlinks in the system that point into the stage.

## Dotfile specialization
This is the workflow for generating specific dotfiles for the current hostname and installing them in the system:

1. Create specific dotfiles by (un)commenting tag-blocks
2. Write them to the stage directory
3. Create symlinks

## Dotfile generalization
The generalized dotfile representation resides in the dotfile repository. Here, all tag-blocks are without comments. Thus, they can be edited using syntax highlighting.
You can create generic dotfiles from the current system, the stage.

## ToDo
* Allow setting the file destination using a comment, i.e. for files in /etc
