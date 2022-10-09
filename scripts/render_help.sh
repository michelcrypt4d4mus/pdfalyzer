#!/bin/bash
# Render the help to an SVG; render that SVG to a .png image
RENDER_HELP_FORMAT=png RENDER_HELP_OUTPUT_DIR=doc/svgs/rendered_images/ pdfalyze --help
