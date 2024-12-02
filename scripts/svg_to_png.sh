#!/usr/bin/env bash
set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

# Use inkscape to render a png for each svg file in doc/svgs/

SCRIPT_DIR="$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")"
SVG_DIR="${SCRIPT_DIR}/../doc/svgs/"
PNG_DIR="${SVG_DIR}/rendered_images/"

# Ensure the output directory exists
mkdir -p "${PNG_DIR}"

# Use find with -print0 and while read loop for better handling of filenames with spaces
find "${SVG_DIR}" -iname "*.svg" -print0 | while IFS= read -r -d '' svg; do
    rendered_png="${PNG_DIR}/$(basename "${svg}").png"
    echo -e "Rendering ${svg}\n       to ${rendered_png}..."
    inkscape --export-filename="${rendered_png}" "${svg}"
done
