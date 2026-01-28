#!/bin/bash -e
# Search the test files in the pypdf repo for a key like /FontFile or whatever
SCRIPT_PATH=$(dirname -- "$(readlink -f -- "$0";)";)
. "$SCRIPT_PATH/lib/project_paths.sh"
set -e


egrep --color -r --text "$1" "$PYPDF_RESOURCES_DIR" "$PYPDF_SAMPLES_DIR"
