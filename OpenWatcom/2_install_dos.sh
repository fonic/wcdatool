#!/usr/bin/env bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic (https://github.com/fonic)                            -
#  Date: 06/16/19 - 01/31/22                                              -
#                                                                         -
#  Based on '2_install_linux.sh'.                                         -
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

# Check if root
#(( ${EUID} == 0 )) || { printe "Only root can do this."; exit 1; }

# Process command line
if [[ "$1" == "" || "$2" == "" ]]; then
	printn "\e[1mUsage:\e[0m   ${0##*/} <install-dir> <wrapper-file>"
	printn "\e[1mExample:\e[0m ${0##*/} /opt/dosbox/drive_c/WATCOM /opt/dosbox/drive_c/WATCOM.BAT"
	exit 2
fi
inst_dir="$1"; inst_base="${1%/*}"; inst_name="${inst_dir##*/}"
wrap_file="$2"; wrap_base="${2%/*}"; wrap_name="${wrap_file##*/}"

# Check if install destinations already exist
printh "Checking install destinations..."
re="^([^ .]{1,8})(\.[^ .]{1,3})?$" # basic, but should be sufficient
[[ "${inst_name}" =~ ${re} ]] || { printe "Error: install directory name '${inst_name}' is not DOS-8.3-compliant, aborting."; exit 1; }
[[ "${wrap_name}" =~ ${re} ]] || { printe "Error: wrapper file name '${wrap_name}' is not DOS-8.3-compliant, aborting."; exit 1; }
[[ -d "${inst_dir}" ]] && { printe "Error: install directory '${inst_dir}' already exists, aborting."; exit 1; }
[[ -f "${wrap_file}" ]] && { printe "Error: wrapper file '${wrap_file}' already exists, aborting."; exit 1; }

# Perform installation
printh "Performing installation..."
trap "printe \"Error: installation failed.\"; exit 1" ERR
mkdir -p "${inst_base}"
cp -r "${SOURCES_DIR}/rel" "${inst_dir}"
rm -rf "${inst_dir}/samples" "${inst_dir}/src" "${inst_dir}/binnt" "${inst_dir}/binnt64" "${inst_dir}/binp" "${inst_dir}/binl" "${inst_dir}/binl64" "${inst_dir}/uninstal.exe" "${inst_dir}/watcom.ico"
mkdir "${inst_dir}/doc"
mv "${inst_dir}"/*.txt "${inst_dir}"/*.doc "${inst_dir}"/*.w32 "${inst_dir}/doc"
mkdir -p "${wrap_base}"
cat > "${wrap_file}" <<-EOF
	@ECHO OFF
	SET WATCOM=C:\\${inst_name}
	SET PATH=%WATCOM%\\BINW;%PATH%
	SET EDPATH=%WATCOM%\\EDDAT
	SET INCLUDE=%WATCOM%\\H
EOF
chmod +x "${wrap_file}"
printg "Installation completed successfully."
