#!/usr/bin/env bash
set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

# Use Inkscape to render a PNG for each SVG file in doc/svgs/

SCRIPT_DIR="$(dirname -- "$(readlink -f -- "$0")")"
readonly SCRIPT_DIR

SVG_DIR="${SCRIPT_DIR}/../doc/svgs/"
readonly SVG_DIR

PNG_DIR="${SVG_DIR}/rendered_images/"
readonly PNG_DIR

# Create PNG_DIR if it doesn't exist
mkdir -p -v "${PNG_DIR}"

# Find and render each SVG file
find "${SVG_DIR}" -iname "*.svg" -print0 | while IFS= read -r -d '' svg; do
    rendered_png="${PNG_DIR}/$(basename "${svg}").png"
    printf "Info: Rendering %s\n       to %s...\n" "${svg}" "${rendered_png}"
    
    if inkscape --export-filename="${rendered_png}" "${svg}"; then
        printf "Info: Successfully rendered %s to %s\n" "${svg}" "${rendered_png}"
    else
        printf "Error: Failed to render %s\n" "${svg}" >&2
        exit 1
    fi
done
