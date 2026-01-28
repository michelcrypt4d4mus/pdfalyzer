#!/bin/bash
# Switch from using PyPi version of yaralyzer to locally checked out repo.
SCRIPT_PATH=$(dirname -- "$(readlink -f -- "$0";)";)
. "$SCRIPT_PATH/lib/project_paths.sh"
set -e


yaralyzer_version=$(egrep '^version' $YARALYZER_PYPROJECT_TOML  | awk '{print $3}')

if [[ -z $yaralyzer_version ]]; then
    echo "Failed to find yaralyzer version." >&2
    exit 1
fi

# git_check_master_branch
update_pyproject_toml "$YARALYZER" "$yaralyzer_version"
poetry lock
poetry install --all-extras
