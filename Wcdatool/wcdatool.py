#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#                                                                         -
#  Watcom Disassembly Tool (wcdatool)                                     -
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 07/29/23                                              -
#                                                                         -
# -------------------------------------------------------------------------


# -------------------------------------
#                                     -
#  TODO                               -
#                                     -
# -------------------------------------

# - Create output directory when missing -> see 'write_file()' in 'module_
#   miscellaneous.py'
#
# - Move code for executable file splitting into functions and/or a separate
#   module


# -------------------------------------
#                                     -
#  Initialization                     -
#                                     -
# -------------------------------------

# Import modules
try:
	import os
	import sys
	import traceback
	import shutil
	import logging
	from modules.module_console_output import *
	from modules.module_argument_parser import *
	from modules.module_logging_setup import *
	from modules.module_miscellaneous import *
	from modules.main_wdump import *
	from modules.main_fixup_relocation import *
	from modules.main_disassembler_gen2 import *
except ImportError as error:
	sys.stderr.write("Error: failed to import required module:\n%s\n" % error)
	sys.exit(1)

# Check Python version
if (sys.version_info < (3, 6, 0)):
	sys.stderr.write("Error: Python >= 3.6.0 is required to run this\n")
	sys.exit(1)


# -------------------------------------
#                                     -
#  Main                               -
#                                     -
# -------------------------------------

# Main function
def main():
	app_title = "Watcom Disassembly Tool (wcdatool)"

	# Set ANSI mode (auto-detection)
	if (sys.stdout.isatty() and sys.stderr.isatty()):
		set_ansi_mode(True)
		if (windows_enable_ansi_terminal() == False):
			set_ansi_mode(False)
	else:
		set_ansi_mode(False)

	# Set window title
	set_window_title(app_title)

	# Process command line
	#parser = ArgumentParser(description="Tool to aid disassembling DOS applications created with the Watcom toolchain.", argument_default=argparse.SUPPRESS, allow_abbrev=False, add_help=False)
	parser = ArgumentParser(description="Tool to aid disassembling DOS applications created with the Watcom toolchain.", allow_abbrev=False, add_help=False)
	parser.add_argument("-wde", "--wdump-exec", action="store", dest="wdump_exec", metavar="PATH", type=str, default="wdump", help="Path to wdump executable")
	parser.add_argument("-ode", "--objdump-exec", action="store", dest="objdump_exec", metavar="PATH", type=str, default="objdump", help="Path to objdump executable")
	parser.add_argument("-wdo", "--wdump-output", action="store", dest="wdump_output", metavar="PATH", type=str, help="Path to file containing pre-generated wdump output to read/parse instead of running wdump")
	parser.add_argument("-wao", "--wdump-addout", action="store", dest="wdump_addout", metavar="PATH", type=str, help="Path to file containing additional wdump output to read/parse (mainly used for object hints)")
	#parser.add_argument("-do", "--data-object", action="store", dest="data_object", metavar="INDEX", type=int, default="auto", help="Index of object 'ds:...' references point to (default: automatic)")
	parser.add_argument("-od", "--output-dir", action="store", dest="output_dir", metavar="PATH", type=str, default=".", help="Path to output directory for storing generated content")
	parser.add_argument("-cm", "--color-mode", action="store", dest="color_mode", metavar="VALUE", type=str.lower, choices=["auto", "true", "false"], default="auto", help="Enable color mode (choices: 'auto', 'true', 'false')")
	parser.add_argument("-id", "--interactive-debugger", action="store_true", dest="ia_debug", help="Drop to interactive debugger before exiting to allow inspecting internal data structures")
	parser.add_argument("-is", "--interactive-shell", action="store_true", dest="ia_shell", help="Drop to interactive shell before exiting to allow inspecting internal data structures")
	parser.add_argument("-h", "--help", action="help", help="Display usage information (this message)")
	parser.add_argument("input_file", action="store", metavar="FILE", type=str, help="Path to input executable to disassemble (.exe file)")
	cmd_args = parser.parse_args()

	# Force-set ANSI mode if requested
	if (cmd_args.color_mode != "auto"):
		set_ansi_mode(True if (cmd_args.color_mode == "true") else False)

	# Set window title
	set_window_title(app_title)

	# Perform additional checks on command line arguments
	checks_errors = []
	if (cmd_args.wdump_output == None and shutil.which(cmd_args.wdump_exec) == None):
		checks_errors.append("wdump executable not found: '%s'" % cmd_args.wdump_exec)
	if (shutil.which(cmd_args.objdump_exec) == None):
		checks_errors.append("objdump executable not found: '%s'" % cmd_args.objdump_exec)
	if (cmd_args.wdump_output != None and not os.path.isfile(cmd_args.wdump_output)):
		checks_errors.append("wdump output file not found: '%s'" % cmd_args.wdump_output)
	if (cmd_args.wdump_addout != None and not os.path.isfile(cmd_args.wdump_addout)):
		checks_errors.append("wdump additional output file not found: '%s'" % cmd_args.wdump_addout)
	if (not os.path.isdir(cmd_args.output_dir)):
		checks_errors.append("output directory not found: '%s'" % cmd_args.output_dir)
	if (not os.path.isfile(cmd_args.input_file)):
		checks_errors.append("input file not found: '%s'" % cmd_args.input_file)
	if (len(checks_errors) > 0):
		sys.stderr.write(parser.format_usage() + "\n")
		for error in checks_errors:
			sys.stderr.write(("Error: %s" % error) + "\n")
		#sys.exit(2)
		return 2

	# Define output file template
	# TODO: use os.path.join() to generate path instead of using os.path.sep
	outfile_template = cmd_args.output_dir + os.path.sep if (cmd_args.output_dir != None) else ""
	outfile_template += os.path.basename(cmd_args.input_file) + "_%s"

	# TODO: create output directory here if missing

	# Set up logging
	# NOTE:
	# If ANSI mode is disabled, different log template including message type is
	# used for console (without this messages would be indistinguishable)
	# TODO:
	# Extend set_up_logging() to create directory path for log file
	try:
		set_up_logging(logger_name=None, console_log_output="stdout", console_log_level="debug", console_log_color=get_ansi_mode(), console_log_template="%(color_on)s%(message)s%(color_off)s" if (get_ansi_mode() == True) else "%(color_on)s%(levelname2)s: %(message)s%(color_off)s", logfile_file=outfile_template % "zzz_log.txt", logfile_log_level="debug", logfile_log_color=False, logfile_log_template="%(color_on)s[%(created)d] [%(levelname)-8s] %(message)s%(color_off)s", logfile_truncate=True)
	except Exception as exception:
		sys.stderr.write("Error: failed to set up logging: %s\n" % str(exception))
		#sys.exit(1)
		return 1

	# Print title
	logging.info(app_title)

	# Print command line
	logging.info("")
	logging.info("Command line:")
	logging.debug("%s %s" % (os.path.basename(sys.argv[0]), str.join(" ", sys.argv[1:])))

	# Parse wdump output
	wdump = wdump_parse_output(cmd_args.input_file, cmd_args.wdump_exec, cmd_args.wdump_output, cmd_args.wdump_addout, outfile_template)
	if (wdump == None):
		return 1

	# Detect and extract DOS/4G(W) stub and payload
	# NOTE: this is necessary as wdump will only yield usable results for the payload
	# TODO: would it make sense to put this in a module? -> 'modules/main_splitter.py'
	if (dict_path_exists(wdump, "dos/16m exe header", "data", "offset of possible next spliced .exp")):
		offset = wdump["dos/16m exe header"]["data"]["offset of possible next spliced .exp"]
		logging.info("")
		logging.info("Extracting DOS/4G(W) stub and payload:")
		logging.debug("Offset of DOS/4G(W) payload: 0x%x" % offset)
		try:
			logging.debug("Opening input file to read data...")
			with open(cmd_args.input_file, "rb") as infile:
				logging.debug("Reading DOS/4G(W) stub data (offset 0x0 - 0x%x)..." % (offset-1))
				stub_data = infile.read(offset)
				logging.debug("Reading DOS/4G(W) payload data (offset 0x%x - EOF)..." % offset)
				payload_data = infile.read()
		except Exception as exception:
			logging.error("Error: %s" % str(exception))
			return 1
		logging.debug("Writing DOS/4G(W) stub data to file (%d bytes)..." % len(stub_data))
		write_file(outfile_template % "split_dos4g_stub.exe", stub_data)
		logging.debug("Writing DOS/4G(W) payload data to file (%d bytes)..." % len(payload_data))
		write_file(outfile_template % "split_dos4g_payload.exe", payload_data)
		cmd_args.input_file = outfile_template % "split_dos4g_payload.exe"
		logging.debug("Re-Running wdump parser for DOS/4G(W) payload...")
		wdump = wdump_parse_output(cmd_args.input_file, cmd_args.wdump_exec, cmd_args.wdump_output, cmd_args.wdump_addout, outfile_template)
		if (wdump == None):
			return 1

	# Detect and extract linear executable stub and payload
	# NOTE: this is solely to allow further examination of the extracted files, they are not used anywhere in this script
	# TODO: would it make sense to put this in a module? -> 'modules/main_splitter.py'
	if (dict_path_exists(wdump, "linear exe header (os/2 v2.x) - le", "data", "file offset")):
		offset = wdump["linear exe header (os/2 v2.x) - le"]["data"]["file offset"]
		logging.info("")
		logging.info("Extracting linear executable stub and payload:")
		logging.debug("Offset of linear executable payload: 0x%x" % offset)
		try:
			logging.debug("Opening input file to read data...")
			with open(cmd_args.input_file, "rb") as infile:
				logging.debug("Reading linear executable stub data (offset 0x0 - 0x%x)..." % (offset-1))
				stub_data = infile.read(offset)
				logging.debug("Reading linear executable payload data (offset 0x%x - EOF)..." % offset)
				payload_data = infile.read()
		except Exception as exception:
			logging.error("Error: %s" % str(exception))
			return 1
		logging.debug("Writing linear executable stub data to file (%d bytes)..." % len(stub_data))
		write_file(outfile_template % "split_linear_executable_stub.exe", stub_data)
		logging.debug("Writing linear executable payload data to file (%d bytes)..." % len(payload_data))
		write_file(outfile_template % "split_linear_executable_payload.bin", payload_data)

	# Read and decode fixup/relocation data
	fixrel = fixup_relocation_read_decode(wdump, cmd_args.input_file, outfile_template)
	if (fixrel == None):
		return 1

	# Disassemble objects
	disasm = disassemble_objects_gen2(wdump, fixrel, cmd_args.objdump_exec, outfile_template)

	# Drop to interactive debugger/shell if requested
	if (cmd_args.ia_debug == True or cmd_args.ia_shell == True):
		logging.info("")
		logging.info("Dropping to interactive %s..." % ("debugger" if cmd_args.ia_debug else "shell"))
		logging.info("Generated data is stored in locals 'wdump', 'fixrel' and 'disasm'.")
		shell_locals={ "wdump": wdump, "fixrel": fixrel, "disasm": disasm }
		if (cmd_args.ia_debug == True):
			import pdb
			pdb.run("", globals=globals(), locals=shell_locals)
		elif (cmd_args.ia_shell == True):
			import code
			code.interact(banner="", local=shell_locals, exitmsg="")

	# All done
	# NOTE: Used to indicate completion when running from within IDE
	print_normal()
	print_good("All done.")

	# Return home safely
	return 0

# Main function wrapper
# NOTE:
# Using try-except construct to ensure application won't exit without asking
# for user confirmation on Microsoft Windows to prevent window from closing
# prematurely, even if an exception occurred or sys.exit() was called
if (__name__ == "__main__"):
	retval = 0
	try:
		retval = main()
	except Exception:
		traceback.print_exc()
		retval = 1
	except SystemExit as systemexit:
		retval = systemexit.code
	except KeyboardInterrupt:
		if (sys.stdout.isatty()):
			sys.stdout.write("\n")
		elif (sys.stderr.isatty()):
			sys.stderr.write("\n")
		retval = 130
	windows_enter_to_exit()
	sys.exit(retval)
