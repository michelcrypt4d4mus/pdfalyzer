#!/bin/bash
SCRIPT_PATH=$(dirname -- "$(readlink -f -- "$0";)";)
source "$SCRIPT_PATH/lib/project_paths.sh"

# Exporting makes these available to the 'find -exec bash -c' invocation
export PDFALYZER_EXECUTABLE
export SUCCESS_LOG=log/successfully_parsed.txt
export FAILURE_LOG=log/failed_to_parse.txt


pdfalyze_doc() {
    pdf_full_path="$(readlink -f "$1")"
    pdf_basename=`basename "$pdf_full_path"`

    if [[ $pdf_basename =~ postgresql.* ]]; then
        echo "Skipping '$pdf_basename'..."  # Postgres PDF takes forever to process
        return
    fi

    cmd="$PDFALYZER_EXECUTABLE -r -t -d \"$pdf_full_path\""
    echo -e "\nCommand to run: $cmd"

    eval $cmd

    if [ $? -eq 0 ]; then
        echo "$pdf_full_path" >> "$SUCCESS_LOG"
    else
        echo "$pdf_full_path" >> "$FAILURE_LOG"
    fi
}

export -f pdfalyze_doc

rm "$SUCCESS_LOG" 2>/dev/null
rm "$FAILURE_LOG" 2>/dev/null
find ~/Documents/ -iname "*.pdf" -type f -exec bash -c 'pdfalyze_doc "{}"' \;
