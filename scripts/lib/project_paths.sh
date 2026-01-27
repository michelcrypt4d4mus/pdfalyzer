#!/bin/bash -e
# From https://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself
set -e

PDFALYZER_SCRIPT_LIB_PATH="${BASH_SOURCE[0]}";
PYPROJECT_TOML=pyproject.toml
SED_BACKUP_EXT=.sedbak

pushd . > /dev/null

while([ -h "${PDFALYZER_SCRIPT_LIB_PATH}" ]); do
    cd "`dirname "${PDFALYZER_SCRIPT_LIB_PATH}"`"
    PDFALYZER_SCRIPT_LIB_PATH="$(readlink "`basename "${PDFALYZER_SCRIPT_LIB_PATH}"`")";
done

cd "`dirname "${PDFALYZER_SCRIPT_LIB_PATH}"`" > /dev/null

PDFALYZE=pdfalyze
PDFALYZER_SCRIPT_LIB_PATH="`pwd`";
PDFALYZER_PROJECT_PATH=$(realpath "$PDFALYZER_SCRIPT_LIB_PATH/../..")
PDFALYZER_PYPROJECT_TOML="$PDFALYZER_PROJECT_PATH/pyproject.toml"
PDFALYZER_TOOLS_DIR="$PDFALYZER_PROJECT_PATH/tools"
PDFALYZER_RENDERED_FIXTURES_DIR="$PDFALYZER_PROJECT_PATH/tests/fixtures"

# Yaralyzer
YARALYZE=yaralyze
YARALYZER=${YARALYZE}r
YARALYZER_REPO_DIR="$PDFALYZER_PROJECT_PATH/../$YARALYZER"
YARALYZER_PYPROJECT_TOML="$YARALYZER_REPO_DIR/$PYPROJECT_TOML"

popd > /dev/null  # TODO wtf?

# Colors
CYAN='\033[0;36m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NO_COLOR='\033[0m'


# Functions
echo_debug() { echo -e "$1"; }
echo_error() { echo -e "${RED}ERROR: ${1}${NO_COLOR}"; }
echo_status() { echo -e "${CYAN}${1}${NO_COLOR}"; }


git_current_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/\1/'
}


git_check_master_branch() {
    local current_branch="$(git_current_branch)"

    if [[ 'master' != $current_branch ]]; then
        echo_error "On $current_branch you can't run this command." >&2
        return 1
    fi
}


update_pyproject_toml() {
    local package_to_update="$1"
    local new_package_version="$2"
    echo_debug "\nupdate_pyproject_toml called with:\n  [1] $1\n  [2] $2\n"

    if [[ ! -f $PYPROJECT_TOML ]]; then
        echo_error "$PYPROJECT_TOML does not exist..."
        return 1
    fi

    if [[ -z $package_to_update ]]; then
        echo_error "No package_to_update provided." >&2
        exit 1
    elif [[ -z $new_package_version ]]; then
        echo_error "No new_package_version provided." >&2
        exit 1
    else
        echo_status "Updating $package_to_update to $new_package_version in $PDFALYZER_PYPROJECT_TOML..."
    fi

    local sed_cmd="s/^$YARALYZER = .*/$YARALYZER = $new_package_version/"
    echo_debug "\n  sed -i $SED_BACKUP_EXT \"$sed_cmd\" $PDFALYZER_PYPROJECT_TOML\n"
    sed -i $SED_BACKUP_EXT "$sed_cmd" "$PDFALYZER_PYPROJECT_TOML"
    rm "${PDFALYZER_PYPROJECT_TOML}${SED_BACKUP_EXT}"
    echo_status "Updated $(basename $PDFALYZER_PYPROJECT_TOML)'s $package_to_update to $new_package_version"
}
