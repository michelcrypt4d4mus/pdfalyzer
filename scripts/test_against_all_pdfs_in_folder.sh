#!/bin/bash
# Takes one argument, the folder to scan for PDFs (scans recursively with 'find')
SCRIPT_PATH=$(dirname -- "$(readlink -f -- "$0";)";)
source "$SCRIPT_PATH/lib/project_paths.sh"


DIR_TO_SCAN="$1"

if [[ ! -d "$DIR_TO_SCAN" ]]; then
    echo_error "'$DIR_TO_SCAN' is not a valid directory."
    exit 1
fi


pdfalyze_doc() {
    local pdf_full_path="$(readlink -f "$DIR_TO_SCAN")"
    local pdf_basename=`basename "$pdf_full_path"`

    if [[ $pdf_basename =~ postgresql.* ]]; then
        echo "Skipping '$pdf_basename'..."  # Postgres PDF takes forever to process
        return
    fi

    cmd="$PDFALYZE -f -r -t \"$pdf_full_path\""
    echo -e "\nCommand to run: $cmd"

    eval $cmd

    if [ $? -eq 0 ]; then
        echo "$pdf_full_path" >> "$SUCCESS_LOG"
    else
        echo "$pdf_full_path" >> "$FAILURE_LOG"
    fi
}


# Exporting makes these available to the 'find -exec bash -c' invocation
export -f pdfalyze_doc
export PDFALYZE
export SUCCESS_LOG=log/successfully_parsed.txt
export FAILURE_LOG=log/failed_to_parse.txt

rm "$SUCCESS_LOG" 2>/dev/null
rm "$FAILURE_LOG" 2>/dev/null
find "$1/" -iname "*.pdf" -type f -exec bash -c 'pdfalyze_doc "{}"' \;
