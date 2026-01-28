#!/bin/bash
# Switch from using PyPi version of yaralyzer to locally checked out repo.
# Takes one arg, if you want to create a new branch and switch to it.
SCRIPT_PATH=$(dirname -- "$(readlink -f -- "$0";)";)
. "$SCRIPT_PATH/lib/project_paths.sh"
set -e

LOCAL_YARALYZER_REQ='{path = "..\/yaralyzer", develop = true}'


local_yaralyzer_branch=$1

if [[ ! -z $local_yaralyzer_branch ]]; then
    echo -e "Creating new branch $local_yaralyzer_branch..."
    git checkout -b $local_yaralyzer_branch
    exit 1
fi

update_pyproject_toml $YARALYZER "$LOCAL_YARALYZER_REQ"
poetry lock
poetry install --all-extras
