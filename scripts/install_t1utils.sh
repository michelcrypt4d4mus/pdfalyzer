#!/bin/bash -e
# Installs the T1Utils suite for working with Adobe Type1 fonts.
# Requires autoconf and automake on macOS.

if cat /etc/*release | grep ^NAME | egrep 'CentOS|Red|Fedora'; then
    echo "Installing t1utils with yum..."
    sudo yum install -y t1utils
    exit 0
elif cat /etc/*release | grep ^NAME | egrep 'Ubuntu|Debian|Mint|Knoppix'; then
    echo "Installing t1utils with apt-get..."
    sudo apt-get install -y t1utils
    exit 0
elif ! echo `uname -a` | grep Darwin 2>&1 >/dev/null; then
    echo "OS NOT DETECTED, couldn't install t1utils"
    exit 1;
fi

echo "macOS detected, building t1utils from source..."


for required_build_tool in automake autoconf make; do
    if ! which $required_build_tool >/dev/null; then
        echo "Missing $required_build_tool. You may need to run something like 'brew install $required_build_tool'."
    fi
done

SCRIPT_PATH=$(dirname -- "$(readlink -f -- "$0";)";)
source "$SCRIPT_PATH/lib/project_paths.sh"
TMP_DIR="$PDFALYZER_PROJECT_PATH/tmp"

mkdir -p "$TMP_DIR"
pushd "$TMP_DIR" >/dev/null
git clone https://github.com/kohler/t1utils.git

cd t1utils
command autoreconf -i
./configure

echo "Successfully configured, building with 'make'..."
make

echo "About to run 'make install' as sudo which will place binaries in /usr/local/bin. You will be asked for your password."
echo "For a different install location you'll need to manually intervene here."
sudo mkdir -p /usr/local/bin
sudo make install

popd >/dev/null
