#!/bin/bash
# Switch from using PyPi version of yaralyzer to locally checked out repo.
set -e

LOCAL_YARALYZER_REQ='{path = "..\/yaralyzer", develop = true}'
PYPROJECT_TOML=pyproject.toml
YARALYZER=yaralyzer

local_yaralyzer_branch=$1


git_current_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/'
}

git_check_master_branch() {
    local current_branch="$(git_current_branch)"

    if [[ 'master' != $current_branch ]]; then
        echo "On $current_branch you can't run this command." >&2
        return 1
    fi
}

update_pyproject_toml() {
    if [[ ! -f $PYPROJECT_TOML ]]; then
        echo "ERROR: $PYPROJECT_TOML does not exist..."
        return 1
    fi

    local sed_cmd="s/^$YARALYZER = .*/$YARALYZER = $LOCAL_YARALYZER_REQ/"
    #echo -e "\n  sed -i .sedbak \"$sed_cmd\" $PROJECT_TOML\n"
    sed -i .sedbak "$sed_cmd" $PYPROJECT_TOML
    rm "$PYPROJECT_TOML.sedbak"
    echo -e "\Updated $PYPROJECT_TOML yaralyzer to point at local dir..."
}


if [[ -z $local_yaralyzer_branch ]]; then
    echo "No branch name provided." >&2
    exit 1
fi


git_check_master_branch
update_pyproject_toml
git checkout -b $local_yaralyzer_branch
poetry lock
poetry install --all-extras
