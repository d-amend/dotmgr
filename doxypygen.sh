#!/bin/sh
# A stupid little wrapper script for doxygen in python projects.
#
# Saves all uncommitted changes and untracked files and filters all Python files
# using the doxypypy filter before calling Doxygen.
# When Doxygen is finished, all changes introduced by the filter are reverted.


# Uncomment to see more SCM output
SCM_VERBOSITY="--quiet"
test -z "$DOXYGEN" && DOXYGEN=doxygen


# Check arguments
if [ $# -lt 1 ]; then
    echo "usage: `basename $0` <path to Doxyfile>"
    echo "You must call this script from the project's root directory."
    exit
fi

# Check if we can use git
git rev-parse 2>/dev/null || {
    echo "Error: This is not a git repository!"
    exit
}

# Check working directory
if [ -n "`git rev-parse --show-prefix`" ]; then
    echo "Error: You must call this script from the project's root directory."
    exit
fi


# Save changes in a git stash
git stash --include-untracked $SCM_VERBOSITY
git stash apply $SCM_VERBOSITY

# Filter python files
temp=`mktemp .$0_XXXXX`
for file in `find dotmgr -type f`
do
    doxypypy --autobrief --autocode $file > $temp
    cat $temp > $file
done
rm $temp

# Call Doxygen
$DOXYGEN $1

# Restore working directory state
git checkout $SCM_VERBOSITY .
git clean -df --exclude='doc' $SCM_VERBOSITY
git stash pop --index $SCM_VERBOSITY
