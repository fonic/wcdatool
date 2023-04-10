#!/usr/bin/env bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/16/19 - 04/09/23                                              -
#                                                                         -
# -------------------------------------------------------------------------

# Configuration
SCRIPT_DIR="$(cd "$(dirname -- "$0")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/open-watcom-v2"
GIT_REPO="https://github.com/open-watcom/open-watcom-v2.git"
#GIT_COMMIT="a69433b2131f8d59adaab9a559e6534ab6495b12" # https://github.com/open-watcom/open-watcom-v2/commit/a69433b2131f8d59adaab9a559e6534ab6495b12
#^ may be used to specify the latest working commit (as build-breaking commits are quite common for the project)

# Print normal/hilite/good/warn/error message [$*: message]
function printn() { echo -e "$*"; }
function printh() { echo -e "\e[1m$*\e[0m"; }
function printg() { echo -e "\e[1;32m$*\e[0m"; }
function printw() { echo -e "\e[1;33m$*\e[0m" >&2; }
function printe() { echo -e "\e[1;31m$*\e[0m" >&2; }

# Backup existing sources
if [[ -d "${BUILD_DIR}" ]]; then
	printh "Backing up existing sources..."
	rm -rf -- "${BUILD_DIR}.old" || { printe "Error: failed to remove old backup directory '${BUILD_DIR}.old', aborting."; exit 1; }
	mv -v -- "${BUILD_DIR}" "${BUILD_DIR}.old" || { printe "Error: failed to move existing sources directory from '${BUILD_DIR}' to '${BUILD_DIR}.old', aborting."; exit 1; }
fi

# Download sources
printh "Downloading sources..."
if [[ -n "${GIT_COMMIT}" ]]; then
	# Full clone + checkout specific revision/commit
	git clone "${GIT_REPO}" "${BUILD_DIR}" || { printe "Error: failed to clone git repository '${GIT_REPO}' to '${BUILD_DIR}', aborting."; exit 1; }
	cd -- "${BUILD_DIR}" || { printe "Error: failed to change directory to '${BUILD_DIR}', aborting."; exit 1; }
	git checkout "${GIT_COMMIT}" || { printe "Error: failed to checkout git commit '${GIT_COMMIT}', aborting."; exit 1; }
else
	# Shallow clone of latest revision/commit
	git clone --depth=1 "${GIT_REPO}" "${BUILD_DIR}" || { printe "Error: failed to clone git repository '${GIT_REPO}' to '${BUILD_DIR}', aborting."; exit 1; }
fi
printg "Download completed succesfully."
