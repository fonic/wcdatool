#!/usr/bin/env bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic (https://github.com/fonic)                            -
#  Date: 06/16/19 - 01/31/22                                              -
#                                                                         -
# -------------------------------------------------------------------------

# Configuration
SCRIPT_DIR="$(cd "$(dirname -- "$0")" && pwd)"
SOURCES_DIR="${SCRIPT_DIR}/open-watcom-v2"
DOWNLOAD_URL="https://github.com/open-watcom/open-watcom-v2.git"

# Print normal/hilite/good/warn/error message [$*: message]
function printn() { echo -e "$*"; }
function printh() { echo -e "\e[1m$*\e[0m"; }
function printg() { echo -e "\e[1;32m$*\e[0m"; }
function printw() { echo -e "\e[1;33m$*\e[0m"; }
function printe() { echo -e "\e[1;31m$*\e[0m"; }

# Backup existing sources
if [[ -d "${SOURCES_DIR}" ]]; then
	printh "Backing up existing sources..."
	rm -rf -- "${SOURCES_DIR}.old" || { printe "Error: failed to remove old backup directory '${SOURCES_DIR}.old', aborting."; exit 1; }
	mv -v -- "${SOURCES_DIR}" "${SOURCES_DIR}.old" || { printe "Error: failed to move existing sources directory from '${SOURCES_DIR}' to '${SOURCES_DIR}.old', aborting."; exit 1; }
fi

# Download sources
printh "Downloading sources..."
git clone --depth=1 "${DOWNLOAD_URL}" "${SOURCES_DIR}" || { printe "Error: failed to download sources from '${DOWNLOAD_URL}' to '${SOURCES_DIR}'."; exit 1; }
printg "Download completed succesfully."
