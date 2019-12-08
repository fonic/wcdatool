#!/bin/bash

# Check command line
[[ "$1" == "" ]] && { echo -e "\e[1mUsage:\e[0m $(basename "$0") <file.exe>"; exit 2; }

# Check if an '..._wao.txt' file exists (e.g. MK1.EXE -> MK1.EXE_wao.txt);
# if so, instruct wcdctool to make use of it
wao="${1}_wao.txt"
if [[ -f "${wao}" ]]; then
    "../Wcdctool/wcdctool.py" --outdir=../Output --wdump-additional-output="${wao}" "$@"
    exit $?
else
    "../Wcdctool/wcdctool.py" --outdir=../Output "$@"
    exit $?
fi
