#!/bin/bash
# Switch from using PyPi version of yaralyzer to locally checked out repo.
SCRIPT_PATH=$(dirname -- "$(readlink -f -- "$0";)";)
. "$SCRIPT_PATH/lib/project_paths.sh"
set -e

LOCAL_YARALYZER_REQ='{path = "..\/yaralyzer", develop = true}'


local_yaralyzer_branch=$1

if [[ -z $local_yaralyzer_branch ]]; then
    echo "No branch name provided." >&2
    exit 1
fi

git_check_master_branch
update_pyproject_toml $YARALZYER "$LOCAL_YARALYZER_REQ"
git checkout -b $local_yaralyzer_branch
poetry lock
poetry install --all-extras
