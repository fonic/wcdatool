#!/bin/bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic (https://github.com/fonic)                            -
#  Date: 06/16/19                                                         -
#                                                                         -
#  Based on '2_install_linux.sh'.                                         -
#                                                                         -
# -------------------------------------------------------------------------

# Check if root
(( ${EUID} == 0 )) || { echo "Only root can do this."; exit 1; }

# Check command line
[[ "$1" != "" ]] || { echo -e "\e[1mUsage:\e[0m   ${0##*/} <dst-dir>"; echo -e "\e[1mExample:\e[0m ${0##*/} /opt/dosbox/drive_c/WATCOM"; exit 2; }

# Check if destination already exists
[[ -d "$1" ]] && { echo -e "\e[1;33mDestination directory '$1' already exists. Aborting.\e[0m"; exit 1; }

# Set error trap
trap "echo -e \"\e[1;33mAn error occured, aborting\e[0m\"; exit 1" ERR

# Perform installation
dst_path="$1"; dst_base="${1%/*}"; dst_dir="${1##*/}"; dst_wrapper="${dst_base}/WATCOM.BAT"
mkdir -p "${dst_base}"
cp -r "open-watcom-v2/rel" "${dst_path}"
rm -rf "${dst_path}/samples" "${dst_path}/src" "${dst_path}/binnt" "${dst_path}/binnt64" "${dst_path}/binp" "${dst_path}/binl" "${dst_path}/binl64" "${dst_path}/uninstal.exe" "${dst_path}/watcom.ico"
mkdir "${dst_path}/doc"; mv "${dst_path}"/*.txt "${dst_path}"/*.doc "${dst_path}"/*.w32 "${dst_path}/doc"
cat > "${dst_wrapper}" <<-EOF
	@ECHO OFF
	SET WATCOM=C:\\${dst_dir}
	SET PATH=%WATCOM%\\BINW;%PATH%
	SET EDPATH=%WATCOM%\\EDDAT
	SET INCLUDE=%WATCOM%\\H
EOF
chmod +x "${dst_wrapper}"
