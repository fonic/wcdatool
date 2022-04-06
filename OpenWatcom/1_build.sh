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

# Print normal/hilite/good/warn/error message [$*: message]
function printn() { echo -e "$*"; }
function printh() { echo -e "\e[1m$*\e[0m"; }
function printg() { echo -e "\e[1;32m$*\e[0m"; }
function printw() { echo -e "\e[1;33m$*\e[0m"; }
function printe() { echo -e "\e[1;31m$*\e[0m"; }

# Check if command is available [$1: command]
function is_command_available() {
	command -v "$1" &>/dev/null
	return $?
}

# Check if DOSEMU or DOSBox is available (Open Watcom defaults to DOSEMU)
printh "Checking availability of DOS emulator..."
if is_command_available "dosemu"; then
	printn "Found DOSEMU (default)"
elif is_command_available "dosbox"; then
	printn "Found DOSBox"
	printn "Modifying 'setvars.sh'..."
	sed -i -- 's/^# export OWDOSBOX=dosbox$/export OWDOSBOX=dosbox/' "${SOURCES_DIR}/setvars.sh" || { printe "Error: failed to modify sources file '${SOURCES_DIR}/setvars.sh', aborting."; exit 1; }
else
	printe "Error: Open Watcom requires either DOSEMU or DOSBox to build, aborting."; exit 1
fi

# Check if path to sources contains space(s)
printh "Checking path to sources..."
if [[ "${SOURCES_DIR}" =~ [[:space:]]+ ]]; then
	printw "Warning: path to Open Watcom sources contains space(s). Build is likely to fail."
	printn "Hit ENTER to continue or CTRL+C to abort"; read -s
fi

# Perform build
printh "Performing build..."
cd -- "${SOURCES_DIR}" && ./build.sh rel || { printe "Error: build failed."; exit 1; }
printg "Build completed succesfully."
