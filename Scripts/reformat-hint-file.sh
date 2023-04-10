#!/usr/bin/env bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 04/09/23                                              -
#                                                                         -
# -------------------------------------------------------------------------

# Configuration
RENUMBER_HINTS="true"
START_INDEX=100
REFORMAT_OFFSETS="true"

# Print normal/hilite/good/warn/error message [$*: message]
function printn() { echo -e "$*"; }
function printh() { echo -e "\e[1m$*\e[0m"; }
function printg() { echo -e "\e[1;32m$*\e[0m"; }
function printw() { echo -e "\e[1;33m$*\e[0m" >&2; }
function printe() { echo -e "\e[1;31m$*\e[0m" >&2; }

# Process command line
if (( $# != 2 )); then
	printn "\e[1mUsage:\e[0m ${0##*/} INFILE OUTFILE"
	exit 2
fi
if [[ "$1" == "$2" ]]; then
	printe "Error: INFILE and OUTFILE must not be the same"
	exit 2
fi
infile="$1"
outfile="$2"

# Process input file, generate output file
re_object="^[[:space:]]*Object [0-9]+:$"
re_hint="^([[:space:]]*)[0-9x]+\)(.*)$"
re_offset="%key% = ([0-9a-fA-F]{8})H"
index=${START_INDEX}
while IFS='' read -r line; do
	if [[ "${line}" =~ ${re_object} ]]; then
		index=${START_INDEX}
	elif [[ "${line}" =~ ${re_hint} ]]; then
		if ${RENUMBER_HINTS}; then
			line="${BASH_REMATCH[1]}${index})${BASH_REMATCH[2]}"
			index=$((index + 1))
		fi
		if ${REFORMAT_OFFSETS}; then
			for key in "offset" "length" "start" "end"; do
				#[[ "${line}" =~ ${re_offset/"%key%"/"${key}"} ]] && line="${line/"${BASH_REMATCH[1]}H"/"${BASH_REMATCH[1],,}H"}"
				[[ "${line}" =~ ${re_offset/"%key%"/"${key}"} ]] && line="${line/"${BASH_REMATCH[1]}H"/"${BASH_REMATCH[1]^^}H"}"
			done
		fi
	fi
	echo "${line}"
done < "${infile}" > "${outfile}"
