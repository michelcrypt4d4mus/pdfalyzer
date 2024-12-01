#!/usr/bin/env bash
set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

# Get Didier Stevens's pdf-parser.py and pdfid.py from github, place them in tools/ dir, and make executable

SCRIPT_PATH="$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")"
. "${SCRIPT_PATH}/lib/project_paths.sh"

TOOL_EXECUTABLES=(pdfid.py pdf-parser.py xorsearch.py)
DIDIER_STEVENS_RAW_GITHUB_URL="https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/"

mkdir -p -v "${PDFALYZER_TOOLS_DIR}"
pushd "${PDFALYZER_TOOLS_DIR}" || exit 1

for tool_executable in "${TOOL_EXECUTABLES[@]}"; do
    wget --secure-protocol=auto --https-only --continue --verbose -N --tries=10 --check-certificate "${DIDIER_STEVENS_RAW_GITHUB_URL}/${tool_executable}"
    chmod 744 "${PDFALYZER_TOOLS_DIR}/${tool_executable}"
done

printf "\n\n\nDidier Stevens recommends always using the -O option with pdf-parser.py. This can be accomplished by setting the PDFPARSER_OPTIONS environment variable:\n\n"
printf "         PDFPARSER_OPTIONS=-O\n\nYou are encouraged to add that to your environment via your .bash_profile or similar.\nThis has NOT been done automatically.\n"
popd || exit 1

