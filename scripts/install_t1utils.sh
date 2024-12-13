#!/usr/bin/env bash
set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

# Installs the T1Utils suite for working with Adobe Type1 fonts.
# Requires autoconf and automake on macOS.

if cat /etc/*release | grep ^NAME | grep -E 'CentOS|Red|Fedora'; then
    printf "Info: Installing t1utils with yum...\n"
    sudo yum install -y t1utils
    exit 0
elif cat /etc/*release | grep ^NAME | grep -E 'Ubuntu|Debian|Mint|Knoppix'; then
    printf "Info: Installing t1utils with apt-get...\n"
    sudo apt-get install -y t1utils
    exit 0
elif ! "$(uname -a)" | grep Darwin >/dev/null 2>&1; then
    printf "Error: OS NOT DETECTED, couldn't install t1utils\n"
    exit 1
fi

printf "Info: macOS detected, building t1utils from source...\n"

for required_build_tool in automake autoconf make; do
    if ! command -v "${required_build_tool}" >/dev/null; then
        printf "Warning: Missing %s. You may need to run something like 'brew install %s'.\n" "${required_build_tool}" "${required_build_tool}"
    fi
done

SCRIPT_PATH="$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")"
# shellcheck source=./lib/project_paths.sh
source "${SCRIPT_PATH}/lib/project_paths.sh"

TMP_DIR="$(mktemp -d -p "${PDFALYZER_PROJECT_PATH}" -t "tmp.XXXXXXXXXX")" || {
    printf "Error: Failed to create temporary directory.\n" >&2
    exit 1
}
pushd "${TMP_DIR}" >/dev/null || exit 1
git clone https://github.com/kohler/t1utils.git

cd t1utils || exit 1
command autoreconf -i
./configure

printf "Info: Successfully configured, building with 'make'...\n"
make

printf "Info: About to run 'make install' as sudo which will place binaries in /usr/local/bin. You will be asked for your password.\n"
printf "Info: For a different install location you'll need to manually intervene here.\n"
sudo mkdir -p -v /usr/local/bin
sudo make install

popd >/dev/null || exit 1
