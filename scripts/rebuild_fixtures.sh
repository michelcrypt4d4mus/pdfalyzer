#!/bin/bash

SCRIPT_PATH=$(dirname -- "$(readlink -f -- "$0";)";)
. "$SCRIPT_PATH/lib/project_paths.sh"


if [ $# -eq 0 ]; then
    echo_status "\nDeleting existing fixtures rendered fixtures from $PDFALYZER_RENDERED_FIXTURES_DIR..."
    rm "$PDFALYZER_RENDERED_FIXTURES_DIR/*.txt"
fi

PYTEST_REBUILD_FIXTURES=True pytest -vv tests/test_pdfalyze.py "$@"
