#!/usr/bin/env bash

# -------------------------------------------------------------------------
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 07/19/23 - 07/21/23                                              -
#                                                                         -
# -------------------------------------------------------------------------

#
# TODO:
# - Add PROJECT_BASEDIR and derive PROJECT_MAIN + PROJECT_MODULES from that
# - Using PROJECT_BASEDIR, recreate the subdirectory structure on-the-fly
#   (instead of hard-coded subdirectory 'modules') -> would allow using the
#   script for other Python projects without any modifications!
#
# NOTE:
#
# - Works well, Wcdatool + modules are compiled successfully
#
# - For now, there is no real benefit (i.e. no performance gain), as this
#   requires modification of the Python sources (mainly decorators and var-
#   iable types)
#   -> see this excellent article for details: https://www.infoworld.com/
#      article/3250299/what-is-cython-python-at-the-speed-of-c.html
#   -> in essence, Cython simply wraps the Python interpreter and Python
#      calls in C, thus Python is still doing all the heavy liftung; only
#      properly decorated functions get translated to native C and can then
#      yield a (significant) performance gain
#
# - Make sure to set PYTHONPATH before running the compiled version (other-
#   wise module imports fail, not entirely sure why):
#   # PYTHONPATH=. ./wcdatool
#
# - This script is not limited to Wcdatool, it should be easily adaptable
#   to other Python projects as well
#
# - An alternative to this script is setting up a 'setup.py' (see testing
#   folder) and then running these commands:
#   # python setup.py build_ext --inplace
#   # cython --embed -o wcdatool.c wcdatool.py
#   # gcc -I /usr/include/python3.11 -l python3.11 -o wcdatool wcdatool.c
#   -> not really any simpler aside from cython automatically handling the
#      compilation of modules
#   -> this script allows for more control and flexibility
#
# Resources:
# https://stackoverflow.com/questions/22507592/making-an-executable-in-cython
# https://stackoverflow.com/questions/22567103/compiling-required-external-modules-with-cython
# https://stackoverflow.com/questions/11507101/how-to-compile-and-link-multiple-python-modules-or-packages-using-cython
# https://stackoverflow.com/questions/46824143/cython-embed-flag-in-setup-py
# https://stackoverflow.com/questions/31307169/how-to-enable-embed-with-cythonize
# https://stackoverflow.com/questions/73027842/cython-embed-on-windows
# https://stackoverflow.com/questions/53904966/how-to-create-python-executable-with-cython-segmentation-fault
#

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="Wcdatool"
PROJECT_MAIN="${SCRIPT_DIR}/../Wcdatool/wcdatool.py"
PROJECT_MODULES=("${SCRIPT_DIR}/../Wcdatool/modules/"*.py)
OUTPUT_DIR="${SCRIPT_DIR}/../Wcdatool/cython"

# Print normal/hilite/good/warn/error message [$*: message]
function printn() { echo -e "$*"; }
function printh() { echo -e "\e[1m$*\e[0m"; }
function printg() { echo -e "\e[1;32m$*\e[0m"; }
function printw() { echo -e "\e[1;33m$*\e[0m" >&2; }
function printe() { echo -e "\e[1;31m$*\e[0m" >&2; }

# Set up error handler
set -ue; trap "printe \"Error: an unhandled error occurred on line \${LINENO}, aborting.\"; exit 1" ERR

# Process command line
if (( $# != 1 )) || [[ "$1" == "-h" || "$1" == "--help" ]]; then
	printn "\e[1mUsage:\e[0m   ${0##*/} PYTHON-VERSION"
	printn "\e[1mExample:\e[0m ${0##*/} 3.11"
	exit 2
fi
python_version="$1"
python_config="python${python_version}-config" # e.g. 'python3.11-config'

# Print what is about to happen, set up cosmetic exit trap
printn
printh "Compiling ${PROJECT_NAME} using Cython + GCC:"
trap "printn" EXIT

# Check availability of required commands
printn
printh "Checking required commands..."
result=0
for cmd in "${python_config}" cython gcc; do
	command -v "${cmd}" || { printe "Error: required command '${cmd}' is not available via PATH"; result=1; }
done
(( ${result} == 0 )) || { printe "Error: missing required commands, aborting."; exit 1; }

# Query 'python*-config' to determine options to be passed to GCC for proper
# compiling and linking
printn
printh "Querying GCC options for Python version ${python_version}..."
result=0
gcc_include="$("${python_config}" --includes)" || { printe "Error: failed to query GCC include options from '${python_config}'"; result=1; }
gcc_linking="$("${python_config}" --libs --embed)" || { printe "Error: failed to query GCC linking options from '${python_config}'"; result=1; }
(( ${result} == 0 )) || { printe "Error: failed to query GCC options from '${python_config}', aborting."; exit 1; }
printn "Include options: ${gcc_include}"
printn "Linking options: ${gcc_linking}"

# Create output directories
printn
printh "Creating output directories..."
mkdir -vp -- "${OUTPUT_DIR}" || { printe "Error: failed to create output directory '${OUTPUT_DIR}', aborting."; exit 1; }
mkdir -vp -- "${OUTPUT_DIR}/modules" || { printe "Error: failed to create output directory '${OUTPUT_DIR}/modules', aborting."; exit 1; }

# Cross-compile main file from Python to C using Cython
# NOTE: options '--embed' instructs cython to generate a main function
result=0
main_pyname="${PROJECT_MAIN##*/}"
main_cname="${main_pyname%".py"}.c"
main_exename="${main_cname%".c"}"
printn
printh "Cross-compiling main from Python '${main_pyname}' to C '${main_cname}'..."
cython -3 --embed -o "${OUTPUT_DIR}/${main_cname}" "${PROJECT_MAIN}" || { printe "Error: failed to cross-compile main from Python '${main_pyname}' to C '${main_cname}'"; result=1; }

# Compile executable from main file's C sources using GCC
if (( ${result} == 0 )); then
	printh "Compiling executable '${main_exename}' from main's C sources '${main_cname}'..."
	#gcc -I "/usr/include/python${python_version}" -l "python${python_version}" -o "${OUTPUT_DIR}/${main_exename}" "${OUTPUT_DIR}/${main_cname}" || { printe "Error: failed to compile executable '${main_exename}' from main's C sources '${main_cname}'"; result=1; }
	gcc ${gcc_include} ${gcc_linking} -o "${OUTPUT_DIR}/${main_exename}" "${OUTPUT_DIR}/${main_cname}" || { printe "Error: failed to compile executable '${main_exename}' from main's C sources '${main_cname}'"; result=1; }
fi

# Cross-compile modules from Python to C using Cython, then compile shared
# objects (.so) from modules' C sources using GCC
for module in "${PROJECT_MODULES[@]}"; do
	printn
	mod_pyname="${module##*/}"
	mod_cname="${mod_pyname%".py"}.c"
	mod_soname="${mod_cname%".c"}.so"
	printh "Cross-compiling module from Python '${mod_pyname}' to C '${mod_cname}'..."
	cython -3 -o "${OUTPUT_DIR}/modules/${mod_cname}" "${module}" || { printe "Error: failed to cross-compile module from Python '${mod_pyname}' to C '${mod_cname}'"; result=1; continue; }
	printh "Compiling module shared object '${mod_soname}' from module's C sources '${mod_cname}'..."
	#gcc -I "/usr/include/python${python_version}" -l "python${python_version}" --shared -fPIC -o "${OUTPUT_DIR}/modules/${mod_soname}" "${OUTPUT_DIR}/modules/${mod_cname}" || { printe "Error: failed to compile module shared object '${mod_soname}' from module's C sources '${mod_cname}'"; result=1; continue; }
	gcc ${gcc_include} ${gcc_linking} --shared -fPIC -o "${OUTPUT_DIR}/modules/${mod_soname}" "${OUTPUT_DIR}/modules/${mod_cname}" || { printe "Error: failed to compile module shared object '${mod_soname}' from module's C sources '${mod_cname}'"; result=1; continue; }
done

# Print and return overall result
printn
(( ${result} == 0 )) && printg "Successfully compiled ${PROJECT_NAME}. Run the compiled version like this (quirk): 'PYTHONPATH=. ./wcdatool'" || printe "Failed to compile ${PROJECT_NAME}."
exit ${result}
