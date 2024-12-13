#!/bin/bash
SCRIPT_PATH="$(dirname -- "$(readlink -f -- "$0")")"
readonly SCRIPT_PATH

source "${SCRIPT_PATH}/lib/project_paths.sh"

# Exporting makes these available to the 'find -exec bash -c' invocation
export PDFALYZER_EXECUTABLE
export SUCCESS_LOG="log/successfully_parsed.txt"
export FAILURE_LOG="log/failed_to_parse.txt"

pdfalyze_doc() {
    local pdf_full_path
    pdf_full_path="$(readlink -f "${1}")"
    readonly pdf_full_path
    local pdf_basename
    pdf_basename="$(basename "${pdf_full_path}")"
    readonly pdf_basename
    
    if [[ "${pdf_basename}" =~ postgresql.* ]]; then
        printf "Info: Skipping '%s'...\n" "${pdf_basename}"  # Postgres PDF takes forever to process
        return
    fi

    local cmd
    cmd="${PDFALYZER_EXECUTABLE} -f -r -t \"${pdf_full_path}\""
    printf "\nInfo: Command to run: %s\n" "${cmd}"

    eval "${cmd}"

    if [[ $? -eq 0 ]]; then
        printf "%s\n" "${pdf_full_path}" >> "${SUCCESS_LOG}"
    else
        printf "%s\n" "${pdf_full_path}" >> "${FAILURE_LOG}"
    fi
}

export -f pdfalyze_doc

# Remove log files if they exist, suppressing errors
rm -f -v "${SUCCESS_LOG}" 2>/dev/null
rm -f -v "${FAILURE_LOG}" 2>/dev/null

find ~/Documents/ -iname "*.pdf" -type f -exec bash -c 'pdfalyze_doc "{}"' \;
