#!/bin/bash
# Render the help to an SVG; render that SVG to a .png image
RENDERED_FILE_BASE=$(basename `git rev-parse --show-toplevel`)_help
RENDERED_SVG="$RENDERED_FILE_BASE.svg"
RENDERED_PNG="doc/svgs/rendered_images/$RENDERED_FILE_BASE.png"

scripts/render_help.py
inkscape --export-filename="$RENDERED_PNG" "$RENDERED_SVG"
rm $RENDERED_SVG
