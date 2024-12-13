#!/usr/bin/env bash
set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

SCRIPT_PATH="$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")"
readonly SCRIPT_PATH
source "${SCRIPT_PATH}/lib/project_paths.sh"

# Exporting makes these available to the 'find -exec bash -c' invocation
export PDFALYZER_EXECUTABLE
export SUCCESS_LOG="log/successfully_parsed.txt"
export FAILURE_LOG="log/failed_to_parse.txt"

pdfalyze_doc() {
    local pdf_full_path
    readonly pdf_full_path
    local pdf_basename
    readonly pdf_basename
    pdf_full_path="$(readlink -f "${1}")"
    pdf_basename="$(basename "${pdf_full_path}")"

    if [[ "${pdf_basename}" =~ postgresql.* ]]; then
        printf "Info: Skipping '%s'...\n" "${pdf_basename}"  # Postgres PDF takes forever to process
        return
    fi

    printf "\nInfo: Command to run: %s -f -r -t \"%s\"\n" "${PDFALYZER_EXECUTABLE}" "${pdf_full_path}"

    if "${PDFALYZER_EXECUTABLE}" -f -r -t "${pdf_full_path}"; then
        echo "${pdf_full_path}" >> "${SUCCESS_LOG}"
    else
        echo "${pdf_full_path}" >> "${FAILURE_LOG}"
    fi
}

export -f pdfalyze_doc

rm -f -v "${SUCCESS_LOG}" 2>/dev/null
rm -f -v "${FAILURE_LOG}" 2>/dev/null

find "${HOME}/Documents/" -iname "*.pdf" -type f -print0 | xargs -0 -I {} bash -c 'pdfalyze_doc "$@"' _ {}
