#!/bin/bash
# poetry claims to be able to do this but I've had some issues crossing platform with the
# generated requirements, so mileage may vary.

poetry export --format requirements.txt --output "${PWD}/requirements.txt" --without-hashes --all-extras
