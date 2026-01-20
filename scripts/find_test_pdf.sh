#!/bin/bash -e
# Search the test files in the pypdf repo for a key like /FontFile or whatever

PYPDF_REPO_DIR="../pypdf"
PYPDF_RESOURCES_DIR="$PYPDF_REPO_DIR/resources/"
PYPDF_SAMPLES_DIR="$PYPDF_REPO_DIR/sample-files/"

egrep --color -r --text "$1" "$PYPDF_RESOURCES_DIR" "$PYPDF_SAMPLES_DIR"
