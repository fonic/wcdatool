#!/usr/bin/env bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/05/22 - 04/09/23                                              -
#                                                                         -
# -------------------------------------------------------------------------

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXECS_DIR="${SCRIPT_DIR}/../Executables"
HINTS_DIR="${SCRIPT_DIR}/../Hints"
OW_WRAPPER_SOURCES="/opt/bin/openwatcom" # default install location of our own scripts
OW_WRAPPER_BINARIES="/usr/bin/watcom/owsetenv.sh" # default install location of binary installer

# Print normal/hilite/good/warn/error message [$*: message]
function printn() { echo -e "$*"; }
function printh() { echo -e "\e[1m$*\e[0m"; }
function printg() { echo -e "\e[1;32m$*\e[0m"; }
function printw() { echo -e "\e[1;33m$*\e[0m" >&2; }
function printe() { echo -e "\e[1;31m$*\e[0m" >&2; }

# Print what's about to happen
printh "Checking available executables..."

# Check availability of wdump utility, try to source Open Watcom environment
# wrapper if not available
if ! command -v wdump >/dev/null; then
	if ! source "${OW_WRAPPER_SOURCES}" 2>/dev/null && ! source "${OW_WRAPPER_BINARIES}" 2>/dev/null; then
		printe "Error: required command 'wdump' is not available via PATH"
		printe "Error: failed to source Open Watcom environment wrapper from '${OW_WRAPPER_SOURCES}' or '${OW_WRAPPER_BINARIES}'"
		exit 1
	fi
fi

# Gather executables and check each one for Watcom-based, MS-Windows, Debug
# Symbols and Object Hints (TODO: Watcom-based + MS-Windows detection might
# not cover all cases, needs more testing/investigation)
readarray -t files < <(find "${EXECS_DIR}" -type f -iname '*.exe' -printf "%f\n" | sort)
for file in "${files[@]}"; do
	output="$(wdump -d -e -q "${EXECS_DIR}/${file}" 2>/dev/null)"
	[[ "${output}" == *"Invalid OS/2, PE header"* ]] && watcom="no" || watcom="yes"
	[[ "${output}" == *"Windows NT EXE Header"* ]] && windows="yes" || windows="no"
	[[ "${output}" == *"No debugging information found"* ]] && debug="no" || debug="yes"
	[[ -f "${HINTS_DIR}/${file}.txt" ]] && hints="yes" || hints="no"
	echo -e "${file}\t${watcom}\t${windows}\t${debug}\t${hints}"
done | column -t -N "Executable,Watcom-based,MS-Windows,Debug Symbols,Object Hints"
