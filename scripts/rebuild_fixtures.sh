#!/bin/bash

SCRIPT_PATH=$(dirname -- "$(readlink -f -- "$0";)";)
. "$SCRIPT_PATH/lib/project_paths.sh"


if [[ -z $PDFALYZER_RENDERED_FIXTURES_DIR ]]; then
    echo_error "PDFALYZER_RENDERED_FIXTURES_DIR not set!"
    exit 1
elif [[ ! -d $PDFALYZER_RENDERED_FIXTURES_DIR ]]; then
    echo_error "PDFALYZER_RENDERED_FIXTURES_DIR $PDFALYZER_RENDERED_FIXTURES_DIR not a dir!"
    exit 1
fi

# Clear fixtures unless there are command line arguments to pass to pytest.
if [ $# -eq 0 ]; then
    echo_status "\nDeleting existing fixtures rendered fixtures from $PDFALYZER_RENDERED_FIXTURES_DIR..."
    set +e
    rm "$PDFALYZER_RENDERED_FIXTURES_DIR/*.txt"
    set -e
fi

PYTEST_REBUILD_FIXTURES=True pytest -vv tests/test_pdfalyze.py "$@"
