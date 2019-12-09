#!/bin/bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic (https://github.com/fonic)                            -
#  Date: 06/16/19                                                         -
#                                                                         -
# -------------------------------------------------------------------------

# Check if command is available [$1: command]
function is_command_available() {
	command -v "$1" &>/dev/null
	return $?
}

# Check if DOSEMU or DOSBox is available (Open Watcom defaults to DOSEMU)
if is_command_available "dosemu"; then
	true
elif is_command_available "dosbox"; then
	sed -i 's/^# export OWDOSBOX=dosbox$/export OWDOSBOX=dosbox/' open-watcom-v2/setvars.sh || exit $?
else
	echo -e "\e[1;33mOpen Watcom requires either DOSEMU or DOSBox to build.\e[0m"
	exit 1
fi

# Check if pwd contains space(s)
re="[[:space:]]+"
if [[ "${PWD}" =~ ${re} ]]; then
	echo -e "\e[1;33mPath to Open Watcom contains space(s). Build is likely to fail.\e[0m"
fi

# Perform build
cd open-watcom-v2 && ./buildrel.sh
exit $?
