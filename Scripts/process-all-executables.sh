#!/usr/bin/env bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 04/06/22                                              -
#                                                                         -
# -------------------------------------------------------------------------

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EXECS_DIR="${SCRIPT_DIR}/../Executables"

# Gather existing executables and run 'process-single-executable.sh' for
# each one of them
readarray -t files < <(find "${EXECS_DIR}" -type f -iname '*.exe' -printf "%f\n" | sort)
for file in "${files[@]}"; do
	"${SCRIPT_DIR}/process-single-executable.sh" "${file}" "$@"
done
