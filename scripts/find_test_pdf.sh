#!/bin/bash -e
# Search the test files in the pypdf repo for a key like /FontFile or whatever
SCRIPT_PATH=$(dirname -- "$(readlink -f -- "$0";)";)
. "$SCRIPT_PATH/lib/project_paths.sh"
set -e


# awk inserts a newline after each change in the filename
grep -E --color -r --text "$1" "$PYPDF_RESOURCES_DIR" "$PYPDF_SAMPLES_DIR" | awk -F: '{if(f!=$1)print ""; f=$1; print $0;}'
