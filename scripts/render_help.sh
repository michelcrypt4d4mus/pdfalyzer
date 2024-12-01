#!/usr/bin/env bash
set -o errexit
set -o errtrace
set -o nounset
set -o pipefail
RENDER_HELP_FORMAT="png" RENDER_HELP_OUTPUT_DIR="doc/svgs/rendered_images/" pdfalyze --help
