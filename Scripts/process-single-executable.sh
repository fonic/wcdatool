#!/usr/bin/env bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 04/09/23                                              -
#                                                                         -
# -------------------------------------------------------------------------

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WCDATOOL_EXEC="${SCRIPT_DIR}/../Wcdatool/wcdatool.py"
OUTPUT_DIR="${SCRIPT_DIR}/../Output"
HINTS_DIR="${SCRIPT_DIR}/../Hints"
EXECS_DIR="${SCRIPT_DIR}/../Executables"
OW_WRAPPER_SOURCES="/opt/bin/openwatcom" # default install location of our own scripts
OW_WRAPPER_BINARIES="/usr/bin/watcom/owsetenv.sh" # default install location of binary installer

# Print normal/hilite/good/warn/error message [$*: message]
function printn() { echo -e "$*"; }
function printh() { echo -e "\e[1m$*\e[0m"; }
function printg() { echo -e "\e[1;32m$*\e[0m"; }
function printw() { echo -e "\e[1;33m$*\e[0m" >&2; }
function printe() { echo -e "\e[1;31m$*\e[0m" >&2; }

# Process command line
if (( $# < 1 )) || [[ "$1" == "-h" || "$1" == "--help" ]]; then
	printn "\e[1mUsage:\e[0m ${0##*/} FILE [OPTIONS]"
	exit 2
fi
file="$1"
opts=("${@:2}")

# Print executable about to be processed
printh "Processing executable '${file}':"

# Check availability of wdump utility, try to source Open Watcom environment
# wrapper if not available
if ! command -v wdump >/dev/null; then
	if ! source "${OW_WRAPPER_SOURCES}" 2>/dev/null && ! source "${OW_WRAPPER_BINARIES}" 2>/dev/null; then
		printe "Error: required command 'wdump' is not available via PATH"
		printe "Error: failed to source Open Watcom environment wrapper from '${OW_WRAPPER_SOURCES}' or '${OW_WRAPPER_BINARIES}'"
		exit 1
	fi
fi
# Check availability of objdump utility
if ! command -v objdump >/dev/null; then
	printe "Error: required command 'objdump' is not available via PATH"
	exit 1
fi

# Build arguments list for wcdatool, look for and add matching hints file
# if existing
WCDATOOL_ARGS=()
WCDATOOL_ARGS+=("-od" "${OUTPUT_DIR}")
if [[ -f "${HINTS_DIR}/${file}.txt" ]]; then
	printn "Hints file: '${HINTS_DIR}/${file}.txt'"
	WCDATOOL_ARGS+=("-wao" "${HINTS_DIR}/${file}.txt")
else
	printw "Hints file: none found (file '${HINTS_DIR}/${file}.txt' does not exist)"
fi
WCDATOOL_ARGS+=("${EXECS_DIR}/${file}")
WCDATOOL_ARGS+=("${opts[@]}")
echo -n "Command line:"; for arg in "${WCDATOOL_EXEC}" "${WCDATOOL_ARGS[@]}"; do [[ "${arg}" == *[[:space:]]* ]] && echo -n " '${arg}'" || echo -n " ${arg}"; done; echo

# Run wcdatool, return result
printn
"${WCDATOOL_EXEC}" "${WCDATOOL_ARGS[@]}"
exit $?
