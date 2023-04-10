#!/usr/bin/env bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 04/09/23                                              -
#                                                                         -
# -------------------------------------------------------------------------

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXECS_DIR="${SCRIPT_DIR}/../Executables"

# Print normal/hilite/good/warn/error message [$*: message]
function printn() { echo -e "$*"; }
function printh() { echo -e "\e[1m$*\e[0m"; }
function printg() { echo -e "\e[1;32m$*\e[0m"; }
function printw() { echo -e "\e[1;33m$*\e[0m" >&2; }
function printe() { echo -e "\e[1;31m$*\e[0m" >&2; }

# Gather executables and run 'process-single-executable.sh' for each one
printh "Processing the following executables:"
readarray -t files < <(find "${EXECS_DIR}" -type f -iname '*.exe' -printf "%f\n" | sort)
for file in "${files[@]}"; do printn "${file}"; done
for file in "${files[@]}"; do printn; "${SCRIPT_DIR}/process-single-executable.sh" "${file}" "$@"; done
