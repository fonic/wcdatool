#!/usr/bin/env bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 04/06/22                                              -
#                                                                         -
# -------------------------------------------------------------------------

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WCDATOOL_FILE="${SCRIPT_DIR}/../Wcdatool/wcdatool.py"
OUTPUT_DIR="${SCRIPT_DIR}/../Output"
HINTS_DIR="${SCRIPT_DIR}/../Hints"
EXECS_DIR="${SCRIPT_DIR}/../Executables"
OW_WRAPPER="/opt/bin/openwatcom"

# Process command line
if (( $# < 1 )) || [[ "$1" == "-h" || "$1" == "--help" ]]; then
	echo "Usage: $(basename "$0") FILE [OPTIONS]"
	exit 2
fi
file="$1"
opts=("${@:2}")

# Check availability of 'wdump' utility, try to source OpenWatcom wrapper
# if not available
if ! command -v wdump >/dev/null; then
	source "${OW_WRAPPER}" || { echo "Error: failed to source OpenWatcom wrapper '${OW_WRAPPER}', aborting."; exit 1; }
fi

# Pick up hints file if existing, run wcdatool
hints="${HINTS_DIR}/${file}.txt"
if [[ -f "${hints}" ]]; then
	"${WCDATOOL_FILE}" -od "${OUTPUT_DIR}" -wao "${hints}" "${EXECS_DIR}/${file}" "${opts[@]}"
else
	"${WCDATOOL_FILE}" -od "${OUTPUT_DIR}" "${EXECS_DIR}/${file}" "${opts[@]}"
fi
exit $?
