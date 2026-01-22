#!/bin/bash -e
# From https://stackoverflow.com/questions/4774054/reliable-way-for-a-bash-script-to-get-the-full-path-to-itself

PDFALYZER_SCRIPT_LIB_PATH="${BASH_SOURCE[0]}";
CYAN='\033[0;36m'
NO_COLOR='\033[0m'

pushd . > /dev/null

while([ -h "${PDFALYZER_SCRIPT_LIB_PATH}" ]); do
    cd "`dirname "${PDFALYZER_SCRIPT_LIB_PATH}"`"
    PDFALYZER_SCRIPT_LIB_PATH="$(readlink "`basename "${PDFALYZER_SCRIPT_LIB_PATH}"`")";
done

cd "`dirname "${PDFALYZER_SCRIPT_LIB_PATH}"`" > /dev/null
PDFALYZER_SCRIPT_LIB_PATH="`pwd`";
PDFALYZER_PROJECT_PATH=$(realpath "$PDFALYZER_SCRIPT_LIB_PATH/../..")
PDFALYZER_TOOLS_DIR="$PDFALYZER_PROJECT_PATH/tools"
PDFALYZER_EXECUTABLE="pdfalyze"
popd > /dev/null


print_status() {
    echo -e "${CYAN}${1}${NO_COLOR}"
}

export -f print_status
