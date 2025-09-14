#!/usr/bin/env bash
set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

# poetry claims to be able to do this but I've had some issues crossing platform with the
# generated requirements, so mileage may vary.

poetry export -f "requirements.txt" --output "${PWD}/requirements.txt" --without-hashes
