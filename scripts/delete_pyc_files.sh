#!/usr/bin/env bash
set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

find .  -name "*.pyc" -delete
