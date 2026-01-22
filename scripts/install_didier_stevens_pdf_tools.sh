#!/bin/bash -e
# Get Didier Stevens's pdf-parser.py and pdfid.py from github, place them in tools/ dir, and make executable
set -e
SCRIPT_PATH=$(dirname -- "$(readlink -f -- "$0";)";)
. "$SCRIPT_PATH/lib/project_paths.sh"

DIDIER_STEVENS_RAW_GITHUB_URL='https://raw.githubusercontent.com/DidierStevens/DidierStevensSuite/master/'
TOOL_EXECUTABLES=(pdfid.py pdf-parser.py xorsearch.py)


mkdir -p "$PDFALYZER_TOOLS_DIR"

for tool_executable in "${TOOL_EXECUTABLES[@]}"; do
    tool_path="$PDFALYZER_TOOLS_DIR/$tool_executable"
    print_status "\nDownloading $tool_executable..."
    curl -o "$tool_path" $DIDIER_STEVENS_RAW_GITHUB_URL/$tool_executable
    print_status " -> Making $tool_path executable..."
    chmod 744 "$tool_path"
done

echo -e "\n\n\nDidier Stevens recommends always using the -O option with pdf-parser.py."
echo -e "This can be accomplished by setting the PDFPARSER_OPTIONS environment variable:\n"
echo -e "         PDFPARSER_OPTIONS=-O\n"
echo -e "You are encouraged to add that to your environment via your .bash_profile or similar."
echo -e "This has NOT been done automatically."
