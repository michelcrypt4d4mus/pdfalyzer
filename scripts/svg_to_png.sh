#!/bin/bash
# Use inkscape to render a png for each svg file in doc/svgs/

SCRIPT_DIR=$(dirname -- "$(readlink -f -- "$0";)";)
SVG_DIR="$SCRIPT_DIR/../doc/svgs/"
PNG_DIR="$SVG_DIR/rendered_images/"


for svg in `find "$SVG_DIR" -iname "*.svg"`; do
    rendered_png="$PNG_DIR/`basename $svg`.png"
    echo -e "Rendering $svg\n       to $rendered_png..."
    inkscape --export-filename="$rendered_png" "$svg"
done
