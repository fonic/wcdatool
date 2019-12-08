#!/bin/bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic (https://github.com/fonic)                            -
#  Date: 06/16/19                                                         -
#                                                                         -
#  Based on user ebuild:                                                  -
#  https://github.com/XVilka/gentoo-overlay/blob/master/dev-lang/         -
#  openwatcom/openwatcom-9999.ebuild                                      -
#  (/usr/local/portage/dev-lang/openwatcom/openwatcom-9999.ebuild)        -
#                                                                         -
#  Based on OpenWatcom documentation:                                     -
#  open-watcom-v2/rel/readme.txt                                          -
#                                                                         -
# -------------------------------------------------------------------------

# Check if root
(( ${EUID} == 0 )) || { echo "Only root can do this."; exit 1; }

# Check command line
[[ "$1" == "" || "$2" == "" ]] && { echo -e "\e[1mUsage:\e[0m   ${0##*/} <install-destination> <wrapper-destination>"; echo -e "\e[1mExample:\e[0m ${0##*/} /opt/openwatcom /opt/bin/openwatcom"; exit 2; }

# Check if destination(s) already exist
[[ -d "$1" ]] && { echo -e "\e[1;33mInstall destination '$1' already exists. Aborting.\e[0m"; exit 1; }
[[ -f "$2" ]] && { echo -e "\e[1;33mWrapper '$2' already exists. Aborting.\e[0m"; exit 1; }

# Set error trap
trap "echo -e \"\e[1;33mAn error occured, aborting\e[0m\"; exit 1" ERR

# Perform installation
ow_path="$1"; ow_base="${1%/*}"
wrapper_path="$2"; wrapper_base="${2%/*}"
mkdir -p "${ow_base}"
cp -r "open-watcom-v2/rel" "${ow_path}"
rm -rf "${ow_path}/samples" "${ow_path}/src" "${ow_path}/binnt" "${ow_path}/binnt64" "${ow_path}/binp" "${ow_path}/uninstal.exe" "${ow_path}/watcom.ico"
mkdir "${ow_path}/doc"; mv "${ow_path}"/*.txt "${ow_path}"/*.doc "${ow_path}"/*.w32 "${ow_path}/doc"
mkdir -p "${wrapper_base}"
cat > "${wrapper_path}" <<-EOF
	#!/bin/bash
	[[ "\${0}" != "\${BASH_SOURCE[0]}" ]] || { echo -e "\e[1mThis script needs to be sourced:\e[0m"; echo "# source \"\${0}\""; exit 1; }
	export WATCOM="${ow_path}"
	export INCLUDE="${ow_path}/lh"
	export EDPATH="${ow_path}/eddat"
	export PATH="\${PATH}:${ow_path}/binl64:${ow_path}/binl"
EOF
chmod +x "${wrapper_path}"
