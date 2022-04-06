#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#                                                                         -
#  Watcom Disassembly Tool (wcdatool)                                     -
#  Main Part Disassembler                                                 -
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 04/06/22                                              -
#                                                                         -
# -------------------------------------------------------------------------


# -------------------------------------
#                                     -
#  TODO                               -
#                                     -
# -------------------------------------

# - See '../../documents/todo-disassembler.txt'
#
# - Below are older TODOs that need to be checked/sorted out (might be out of date):
#
# TODO (make all blocks self-sufficient, as order is not yet finalized; '+': done, '/': partial, '-': open):
# + process references in fixup/relocation data, add to globals
# + process objects, build data maps from object hints describing which parts of object's binary data represent what (code, data + data type)
# / process code objects, process data map, generate plain disassembly
# / process code objects, process plain disassembly, analyze branches (but only those with constant addresses!), add to globals
# / process code objects, process plain disassembly, analyze fixup/relocation references and determine data/access size (WORD, DWORD, etc.), add size information to globals
# - process data objects, generate plain disassembly; make use of information about data sizes stored in globals
# / process objects, create structure (object start/end, modules start/end, functions, variables, ...); add links to globals for filling in missing information (see next item)
# / process objects, process structure, fill in missing information (names, labels, etc.); also fill in information for linked globals; remove links
# / process objects, generate formatted disassembly
# / split disassembly into separate files based on modules, each file containing both code + data
#   -> this requires an offset -> disassembly line map
#   -> it would be easiest to create this map in generate_formatted_disassembly()

# TODO when everything else is done and in order:
# - split huge function 'disassemble_objects()' into sub-functions (might expose errors related to using local variables)
# - rename 'object' to 'object_', 'type' to 'type_', 'global' to 'global_' to avoid reserved words and related side-effects
# - change handling of plain disassembly (huge impact, backup before doing this!):
#   - don't store plain assembly as text lines, instead split lines and store as dicts: OrderedDict([ ("start", 0x...), ("end", 0x...), ("length": ...), ("data": b'...'), ("command", "..."), ("arguments", "..."), ("comment", "...") ])
#   - change generate_define_byte(), generate_data_disassembly() to generate dicts instead of text lines
#   - store new disassembly as object["disassembly"], store structure as object["structure"], drop everything else (i.e. don't store formatted disassembly in object)
#   -> eliminates the need to split asm lines again and again for analysis
#   -> enables us to generate final formatted output with only one single template
#   -> function split_asm_line() can be dropped, as we now only need to split line once in generate_code_disassembly()


# -------------------------------------
#                                     -
#  Exports                            -
#                                     -
# -------------------------------------

__all__ = [ "disassemble_objects" ]


# -------------------------------------
#                                     -
#  Imports                            -
#                                     -
# -------------------------------------

import os
import tempfile
import subprocess
import re
import ntpath
import textwrap
import logging
from collections import OrderedDict
from modules.module_miscellaneous import *
from modules.module_pretty_print import *


# -------------------------------------
#                                     -
#  Code                               -
#                                     -
# -------------------------------------

# Split assembly line (objdump format)
def split_asm_line(line):
	if (not isinstance(line, str)):
		raise TypeError("line must be type str, not %s" % type(line).__name__)

	# Regex: (.*?) non-greedy, (;.*)? optional capturing group
	#match = re.match("^([ ]*)([0-9a-fA-F]+):[ \t]+([0-9a-fA-F ]+)[ \t]+([^ ]+)[ ]*(.*?)\s*(;.*)?$", line) # tabs replaced with '[ \t]+'; objdump output comes with tabs, but we later replace those with spaces
	match = re.match("^([ ]*)([0-9a-fA-F]+):\t([0-9a-fA-F ]+)\t([^ ]+)[ ]*(.*?)\s*(;.*)?$", line)
	if (match):
		return OrderedDict([("indent", match.group(1)), ("offset", int(match.group(2), 16)), ("data", bytes.fromhex(match.group(3).strip())), ("command", match.group(4)), ("arguments", match.group(5)), ("comment", match.group(6))])
	return None


# Check if byte value (integer of range 0-255) is within ASCII range (https://www.asciitable.com/)
#def is_ascii(value, *, only_printable=False):
#	if (not isinstance(value, int)):
#		raise TypeError("value must be type int, not %s" % type(value).__name__)
#	if (not value in range(0, 256)):
#		raise ValueError("value must be within range 0-255, not %d" % value)
#	if (not isinstance(only_printable, bool)):
#		raise TypeError("only_printable must be type bool, not %s" % type(only_printable).__name__)
#
#	if (only_printable == True):
#		if ((value in (7, 8, 9, 10, 11, 12, 13, 27)) or (value in range(32, 127))):
#			return True
#	else:
#		if (value in range(0, 128)):
#			return True
#	return False


# Generate define byte (db) assembly line (objdump format)
def generate_define_byte(offset, value, *, comment=False):
	if (not isinstance(offset, int)):
		raise TypeError("offset must be type int, not %s" % type(offset).__name__)
	if (offset < 0):
		raise ValueError("offset must be positive value, not %s" % offset)
	if (not isinstance(value, int)):
		raise TypeError("value must be type int, not %s" % type(value).__name__)
	if (not value in range(0, 256)):
		raise ValueError("value must be within range 0-255, not %d" % value)
	if (not isinstance(comment, bool)):
		raise TypeError("comment must be type bool, not %s" % type(comment).__name__)

	#result = "%8x:\t%02x                   \t%-6s 0x%02x" % (offset, value, "db", value)
	#result = "%8x:  %-20.02x   %-6s 0x%02x" % (offset, value, "db", value) # tabs replaced with '  '
	result = "%8x:\t%-20.02x \t%-6s 0x%02x" % (offset, value, "db", value)
	if (comment == True):
		if (value == 0):
			char = "\\0"
		elif (value == 7):
			char = "\\a"
		elif (value == 8):
			char = "\\b"
		elif (value == 9):
			char = "\\t"
		elif (value == 10):
			char = "\\n"
		elif (value == 11):
			char = "\\v"
		elif (value == 12):
			char = "\\f"
		elif (value == 13):
			char = "\\r"
		elif (value == 27):
			char = "\\e"
		elif (value >= 32 and value <= 126):
			char = chr(value)
		else:
			char = ""
		#if (value > 0):
		#	#result += "    ; dec: %3d, chr: '%s'" % (value, char)
		#	result = "%-100s; dec: %3d, chr: '%s'" % (result, value, char)
		result = "%-100s; dec: %3d, chr: '%s'" % (result, value, char)
	return result


# Generate disassembly of binary data (bytes, bytearray or memoryview) inter-
# preted as code. Begins at start_ofs, stops when offset >= end_ofs or offset
# >= len(data). Returns offset, length, disassembly (list of strings) and bad
# code sections (list of dicts)
# NOTE:
# Mode argument currently unused, added to be compatible to object hint format
# and generate_data_disassembly(); might be useful in the future in case we need
# different ways to disassemble code
def generate_code_disassembly(data, start_ofs, end_ofs, mode, objdump_exec, line_num, bad_num, verbose=False):
	if (not (isinstance(data, bytes) or isinstance(data, bytearray) or isinstance(data, memoryview))):
		raise TypeError("data must be type bytes, bytearray or memoryview, not %s" % type(data).__name__)
	if (not isinstance(start_ofs, int)):
		raise TypeError("start offset must be type int, not %s" % type(start_ofs).__name__)
	if (start_ofs < 0):
		raise ValueError("start offset must be positive value, not %s" % start_ofs)
	if (not isinstance(end_ofs, int)):
		raise TypeError("end offset must be type int, not %s" % type(end_ofs).__name__)
	if (end_ofs < 0):
		raise ValueError("end offset must be positive value, not %s" % end_ofs)
	if (not isinstance(mode, str)):
		raise TypeError("mode must be type str, not %s" % type(mode).__name__)
	if (not mode in ("default")):
		raise ValueError("invalid mode: '%s'" % mode)
	if (not isinstance(objdump_exec, str)):
		raise TypeError("objdump executable must be type str, not %s" % type(objdump_exec).__name__)
	if (not isinstance(bad_num, int)):
		raise TypeError("bad number must be type int, not %s" % type(bad_num).__name__)
	if (bad_num < 0):
		raise ValueError("bad number must be positive value, not %s" % bad_num)

	# Storage for results
	offset = start_ofs
	length = 0
	disassembly = []
	bad_list = []

	# Write data to temporary file (necessary as objdump will only read from files)
	if (verbose == True): logging.debug("Writing data to temporary file...")
	tmpfile = tempfile.NamedTemporaryFile(mode="w+b", delete=False)
	tmpfile.write(data)
	tmpfile.close()

	# Disassembly loop (loops whenever bad code is detected)
	data_len = len(data)
	while_again = True
	while (while_again == True and offset < data_len and offset < end_ofs):
		while_again = False

		# Run objdump, fetch output
		#logging.debug("Disassembling code from offset 0x%x to offset 0x%x (mode: %s)..." % (offset, end_ofs, mode))
		command = [objdump_exec, "--disassemble-all", "--disassemble-zeroes", "--wide", "--architecture=i386", "--disassembler-options=intel,i386", "--target=binary", "--start-address=0x%x" % offset, "--stop-address=0x%x" % end_ofs, tmpfile.name]
		if (verbose == True): logging.debug("Running command '%s'..." % str.join(" ", command))
		try:
			sub_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
		except Exception as exception:
			logging.error("Error: failed to run command: %s" % str(exception))
			break
		if (sub_process.returncode != 0):
			logging.error("Error: command failed with exit code %d:" % sub_process.returncode)
			logging.error(sub_process.stdout if (sub_process.stdout != "") else "<no output>")
			break
		output = sub_process.stdout.splitlines()

		# Reduce output to actual code listing
		for i in range(0, len(output)):
			if (re.match("^([0-9a-fA-F]+) <.data(\+0x[0-9a-fA-F]+)?>:$", output[i])):
				output = output[i+1:]
				break

		# Process output, add to disassembly, detect bad code
		if (verbose == True): logging.debug("Processing command output (%d lines)..." % len(output))
		for i in range(0, len(output)):
			line = output[i]
			# Replace tabs after offset and hex data with '  ' (as tabs mess with
			# indentation when comments are added later on, e.g. for fixups)
			# FIXME: this is desirable, but make lots of problems for split_asm_line(),
			#        thus disabled for now; we'll come back to this when migrating from
			#        text lines to dicts, i.e. when only one initial split takes place
			#line = line.replace(":\t", ":  ") # tab after '<offset>:'
			#line = line.replace(" \t", "  ")  # tab after hex data
			#line = line.replace("\t", "  ") # replace tabs after offset and hex data with '  '
			disassembly.append(line)

			asm = split_asm_line(line)
			if (asm == None):
				logging.warning("Invalid assembly line: line %d: '%s'" % (i+1, line))
				continue
			offset = asm["offset"] + len(asm["data"])
			length += len(asm["data"])

			# Detect bad code: if ret or jmp is followed by zero(s), find first non-zero
			# byte after command and continue disassembling from that point on; add zero(s)
			# back as padding data
			# NOTE:
			# So far we have only seen those at the very end of modules and objects. Thus,
			# presumably, module starts/ends and object ends/sizes have to adhere to some
			# form of alignment
			if ((asm["command"] == "ret" or asm["command"] == "jmp") and offset < data_len and offset < end_ofs and data[offset] == 0):
				bad_num += 1
				bad_start = offset
				bad_end = offset
				bad_length = 0
				bad_type = "zero after ret" if (asm["command"] == "ret") else "zero after jmp" if (asm["command"] == "jmp") else "unknown"
				bad_line = max(line_num + len(disassembly) - 1, 0)
				bad_context = ([output[i-1]] if (i > 0) else []) + ([output[i], output[i+1], output[i+2]] if (i < len(output)-2) else [output[i], output[i+1]] if (i < len(output)-1) else [output[i]])
				while (offset < data_len and offset < end_ofs and data[offset] == 0):
					disassembly.append(generate_define_byte(offset, data[offset], comment=False))
					bad_length += 1
					offset += 1
					length += 1
				bad_end = offset
				bad_list.append(OrderedDict([("num", bad_num), ("start", bad_start), ("end", bad_end), ("length", bad_length), ("type", bad_type), ("context", bad_context)]))

				if (verbose == True): logging.warning("Bad code: num: %d, start offset: 0x%x, end offset: 0x%x, length: %d, type '%s', context:" % (bad_num, bad_start, bad_end, bad_length, bad_type))
				for j in range(0, len(bad_context)):
					if (verbose == True): logging.warning("line %d: %s" % (bad_line+j, bad_context[j]))

				if (offset < data_len and offset < end_ofs):
					if (verbose == True): logging.warning("Continuing disassembly at offset 0x%x..." % offset)
					while_again = True
				else:
					if (verbose == True): logging.warning("Reached end of data at offset 0x%x." % offset)
				break # break for-loop -> next iteration of 'while (while_again == True)' loop

	# Remove temporary file
	if (verbose == True): logging.debug("Removing temporary file...")
	os.remove(tmpfile.name)

	# Return results
	return (offset, length, disassembly, bad_list)


# Generate disassembly of binary data (bytes, bytearray or memoryview) inter-
# preted as data. Begins at start_ofs, stops when offset >= end_ofs or offset
# >= len(data). Returns offset, length and disassembly (list of strings)
def generate_data_disassembly(data, start_ofs, end_ofs, mode):
	if (not (isinstance(data, bytes) or isinstance(data, bytearray) or isinstance(data, memoryview))):
		raise TypeError("data must be type bytes, bytearray or memoryview, not %s" % type(data).__name__)
	if (not isinstance(start_ofs, int)):
		raise TypeError("start offset must be type int, not %s" % type(start_ofs).__name__)
	if (start_ofs < 0):
		raise ValueError("start offset must be positive value, not %s" % start_ofs)
	if (not isinstance(end_ofs, int)):
		raise TypeError("end offset must be type int, not %s" % type(end_ofs).__name__)
	if (end_ofs < 0):
		raise ValueError("end offset must be positive value, not %s" % end_ofs)
	if (not isinstance(mode, str)):
		raise TypeError("mode must be type str, not %s" % type(mode).__name__)
	if (not mode in ("default", "auto-strings", "strings", "string", "bytes", "words", "dwords", "fwords", "qwords")):
		raise ValueError("invalid mode: '%s'" % mode)

	# Storage for results
	offset = start_ofs
	length = 0
	disassembly = []

	data_len = len(data)
	#asm_template = "%8x:  %-20s   %-6s %s"					# <offset>:  <hex-data>   <define-cmd> <value>; tabs replaced with '  '
	asm_template = "%8x:\t%-20s \t%-6s %s"					# <offset>:\t<hex-data> \t<define-cmd> <value>

	#logging.debug("Disassembling data from offset 0x%x to offset 0x%x (mode: %s)..." % (start_ofs, end_ofs, mode))

	if (mode == "default"):									# Default mode
		mode = "bytes"

	if (mode == "auto-strings"): 							# ASCII string auto-detection + bytes
		min_len = 3											# minimum string length (excluding trailing '\0' if need_null == True)
		need_null = True									# do strings have to be null-terminated?
		strings = []
		hints = []
		#hint_template = "x) start = %08XH, end = %08XH, type = data, mode = string, comment = String"
		hint_template = "x) offset = %08XH, length = %08XH, type = data, mode = string, comment = String"
		while (offset < data_len and offset < end_ofs):
			is_candidate = False
			if (offset < data_len - min_len and offset < end_ofs - min_len): # possible candidate if min_len further bytes are available and within ASCII range
				is_candidate = True
				for ofs in range(offset, offset + min_len):
					#if (not is_ascii(data[ofs], only_printable=True)):
					#if (not data[ofs] in range(1, 127)):
					if (not ((data[ofs] in (7, 8, 9, 10, 11, 12, 13, 27)) or (data[ofs] in range(32, 127)))):
						is_candidate = False
						break
			if (is_candidate == True):
				line_ofs = offset
				is_string = True
				str_parts = []
				values = []
				while (offset < data_len and offset < end_ofs):
					value = data[offset]
					values.append(value)

					#if (value > 127):						# non-ASCII range
					#	if (need_null == True):				# null-termination required -> false positive, not a string; null-termination not required -> string
					#		is_string = False
					#	else:								# null-termination not required -> string is complete; last value has to be removed (was added before if, but is not part of string)
					#		values.pop()
					#		#offset = max(offset - 1, 0)
					#	break
					#elif (value >= 32 and value <= 126):	# ASCII printable range
					#	if (len(str_parts) == 0 or isinstance(str_parts[-1], int)):
					#		str_parts.append("")			# add new string part
					#	str_parts[-1] += chr(value)			# add to last string part
					#else:									# ASCII non-printable range
					#	str_parts.append(value)

					if (value >= 32 and value <= 126):		# ASCII printable range
						if (len(str_parts) == 0 or isinstance(str_parts[-1], int)):
							str_parts.append("")			# add new string part
						str_parts[-1] += chr(value)			# add to last string part
					#elif (value in (0, 7, 8, 9, 10, 13)):	# ASCII non-printable range (reduced to those that one would expect to be actually used in a string)
					elif (value in (0, 7, 8, 9, 10, 11, 12, 13, 27)):	# ASCII non-printable range (reduced to those that one would expect to be actually used in a string)
						str_parts.append(value)
					else:									# everything else
						if (need_null == True):				# null-termination required -> false positive, not a string; null-termination not required -> string
							is_string = False
						else:								# null-termination not required -> string is complete
							values.pop()					# last value has to be removed (was added before if, but is not part of string)
							#offset = max(offset - 1, 0)
						break

					offset += 1
					if (value == 0):						# '\0' -> end of string reached
						break
				if (need_null == True and len(values) > 0 and values[-1] != 0): # null-terminated?
					is_string = False
				if (is_string == True):
					str_str = str.join(",", [ "0x%02x" % part if isinstance(part, int) else "\"%s\"" % part for part in str_parts ])
					hex_str = str.join(" ", [ "%02x" % value for value in values ])
					#hint_str = hint_template % (line_ofs, line_ofs + len(values))
					hint_str = hint_template % (line_ofs, len(values))
					#logging.debug("Found string: '%s', hint: '%s'" % (str_str, hint_str))
					strings.append(str_str)
					hints.append(hint_str)
					disassembly.append(asm_template % (line_ofs, hex_str, "db", str_str))
					length += len(values)
					continue
				for ofs in range(line_ofs, offset):			# string turned out to be false positive -> decode data as bytes
					disassembly.append(generate_define_byte(ofs, data[ofs], comment=True))
					length += 1
				continue
			disassembly.append(generate_define_byte(offset, data[offset], comment=True)) # decode data as bytes
			length += 1
			offset += 1
		###logging.debug("Auto-detected strings:")
		###if (len(strings) > 0):
		###	for string in strings: logging.debug(string)
		###else:
		###	logging.debug("(none)")
		###logging.debug("Hints for strings:")
		###if (len(hints) > 0):
		###	for hint in hints: logging.debug(hint)
		###else:
		###	logging.debug("(none)")
		##if (len(strings) > 0):
		##	logging.debug("Auto-detected strings:")
		##	for string in strings: logging.debug(string)
		##if (len(hints) > 0):
		##	logging.debug("Hints for strings:")
		##	for hint in hints: logging.debug(hint)
		#for string in strings:
		#	logging.debug(string)

	elif (mode == "strings"):								# null-terminated strings (may or may not be ASCII)
		while (offset < data_len and offset < end_ofs):
			line_ofs = offset
			str_parts = []
			values = []
			while (offset < data_len and offset < end_ofs):
				value = data[offset]
				values.append(value)
				if (value >= 32 and value <= 126):			# ASCII printable range
					if (len(str_parts) == 0 or isinstance(str_parts[-1], int)):
						str_parts.append("")
					str_parts[-1] += chr(value)
				else:										# everything else
					str_parts.append(value)
				offset += 1
				if (value == 0):							# by doing it like this, last string does not have to be null-terminated
					break
			str_str = str.join(",", [ "0x%x" % part if isinstance(part, int) else "\"%s\"" % part for part in str_parts ])
			hex_str = str.join(" ", [ "%02x" % value for value in values ])
			disassembly.append(asm_template % (line_ofs, hex_str, "db", str_str))
			length += len(values)

	elif (mode == "string"):								# one single string (may or may not be ASCII and/or null-terminated)
		line_ofs = offset
		str_parts = []
		values = []
		while (offset < data_len and offset < end_ofs):
			value = data[offset]
			values.append(value)
			if (value >= 32 and value <= 126):				# ASCII printable range
				if (len(str_parts) == 0 or isinstance(str_parts[-1], int)):
					str_parts.append("")
				str_parts[-1] += chr(value)
			else:											# everything else
				str_parts.append(value)
			offset += 1
		str_str = str.join(",", [ "0x%x" % part if isinstance(part, int) else "\"%s\"" % part for part in str_parts ])
		hex_str = str.join(" ", [ "%02x" % value for value in values ])
		disassembly.append(asm_template % (line_ofs, hex_str, "db", str_str))
		length += len(values)

	elif (mode == "bytes"):									# bytes
		while (offset < data_len and offset < end_ofs):
			disassembly.append(generate_define_byte(offset, data[offset], comment=True))
			length += 1
			offset += 1

	# TODO: not sure if this works correctly for FWORDS as those are different
	#       (6 bytes, 4 bytes 32-bit offset + 2 bytes 16-bit selector); we have
	#       yet to see some FWORDs in real code to verify this
	elif (mode in ("words", "dwords", "fwords", "qwords")):	# words, dwords, fwords, qwords
		mode_defines = { "words": "dw", "dwords": "dd", "fwords": "df", "qwords": "dq" }
		mode_sizes = { "words": 2, "dwords": 4, "fwords": 6, "qwords": 8 }
		mode_define = mode_defines[mode]
		mode_size = mode_sizes[mode]
		while (offset < data_len and offset < end_ofs):
			if (offset < data_len - mode_size and offset <= end_ofs - mode_size):
				values = list(data[offset:offset+mode_size])
				hex_str = str.join(" ", [ "%02x" % value for value in values ])
				val_str = "0x" + str.join("", [ "%02x" % value for value in reversed(values) ])
				disassembly.append(asm_template % (offset, hex_str, mode_define, val_str))
				length += mode_size
				offset += mode_size
			else:
				disassembly.append(generate_define_byte(offset, data[offset], comment=True))
				length += 1
				offset += 1

	# Return results
	return (offset, length, disassembly)


# Generate disassembly of binary data (bytes, bytearray or memoryview) inter-
# preted as structured data. Begins at start_ofs, stops when offset >= end_ofs
# or offset >= len(data). Returns offset, length and disassembly (list of
# strings)
# NOTE: this is basically an elaborate wrapper for generate_data_disassembly()
def generate_struct_disassembly(data, start_ofs, end_ofs, mode):
	if (not (isinstance(data, bytes) or isinstance(data, bytearray) or isinstance(data, memoryview))):
		raise TypeError("data must be type bytes, bytearray or memoryview, not %s" % type(data).__name__)
	if (not isinstance(start_ofs, int)):
		raise TypeError("start offset must be type int, not %s" % type(start_ofs).__name__)
	if (start_ofs < 0):
		raise ValueError("start offset must be positive value, not %s" % start_ofs)
	if (not isinstance(end_ofs, int)):
		raise TypeError("end offset must be type int, not %s" % type(end_ofs).__name__)
	if (end_ofs < 0):
		raise ValueError("end offset must be positive value, not %s" % end_ofs)
	if (not isinstance(mode, str)):
		raise TypeError("mode must be type str, not %s" % type(mode).__name__)
	if (not mode.startswith("struct:")):
		raise ValueError("invalid mode: '%s'" % mode)
	if (mode.split(":") == ["struct", ""]):
		raise ValueError("mode does not contain any struct member: '%s'" % mode)

	# Split mode string, process struct members, generate struct list
	type_sizes_array = { "chars": 1, "bytes": 1, "words": 2, "dwords": 4, "fwords": 6, "qwords": 8 }
	type_sizes_single = { "char": 1, "byte": 1, "word": 2, "dword": 4, "fword": 6, "qword": 8 }
	struct_list = []
	struct_members = mode.split(":")[1:]
	for item in struct_members:

		# Array types
		match = re.match("^(chars|bytes|words|dwords|fwords|qwords)\[([0-9]+)\]$", item)
		if (match):
			type_ = match.group(1)
			count = int(match.group(2))
			size = type_sizes_array[type_]
			struct_list.append(OrderedDict([("mode", "string" if (type_ == "chars") else type_), ("length", size * count)]))

		# Single types
		elif (item in ("char", "byte", "word", "dword", "fword", "qword")):
			type_ = item
			count = 1
			size = type_sizes_single[type_]
			struct_list.append(OrderedDict([("mode", "string" if (type_ == "char") else type_+"s"), ("length", size * count)]))

		# Invalid struct member
		else:
			raise ValueError("mode contains invalid struct member: '%s'" % item)

	# Decode structured data by repeatedly processing struct list until end of
	# data or end offset reached (each iteration of outer while-loop decodes one
	# full struct, each iteration of inner for-loop decodes one struct member)
	# TODO: should we break when struct member failed to decode?
	offset = start_ofs; length = 0; disassembly = []
	data_len = len(data)
	while (offset < data_len and offset < end_ofs):
		for item in struct_list:
			(offset, length2, disassembly2) = generate_data_disassembly(data, offset, offset + item["length"], item["mode"])
			length += length2; disassembly += disassembly2
			if (length2 != item["length"]):
				logging.warning("Failed to decode struct member: offset: 0x%x, length: 0x%x (%d), mode: %s" % (offset, item["length"], item["length"], item["mode"]))
				#break

	# Return results
	return (offset, length, disassembly)


# Inserts item into sorted structure; maintains sort order, returns inserted item
#
# Insertion modes:
# 'default': inserts after existing items with equal offset
# 'start':   inserts after existing items with equal offset, but before variables with equal offsets (for start items; see e.g. hint start for 'RAND' in object 2 of 'MK1_NO_DOS4GW.EXE')
# 'end':     inserts before existing items with equal offset, starts looking for insertion point after start_item (for end items; see e.g. hint ends in object 2 of 'MK1_NO_DOS4GW.EXE')
#
# NOTE:
# Item dict must contain key-value pairs ('type': <str>), ('offset': <int>), ('name': <str>|None) and ('label': <str>|None)
def insert_structure_item(structure, item, *, ins_mode="default", start_item=None):
	if (not isinstance(structure, list)):
		raise TypeError("structure must be type list, not %s" % type(structure).__name__)
	if (not isinstance(item, dict)):
		raise TypeError("item must be type dict, not %s" % type(item).__name__)
	#for (key, key_type) in (("type", str), ("offset", int), ("name", str), ("label", str)):
	#	if (not key in item):
	#		raise ValueError("item dict does not contain key '%s'" % key)
	#	if (not isinstance(item[key], key_type)):
	#		raise TypeError("item[\"%s\"] must be type %s, not %s" % (key, key_type.__name__, type(item[key]).__name__))
	for (key, key_type) in (("type", str), ("start", int)):
		if (not key in item):
			raise ValueError("item dict does not contain key '%s'" % key)
		if (not isinstance(item[key], key_type)):
			raise TypeError("item[\"%s\"] must be type %s, not %s" % (key, key_type.__name__, type(item[key]).__name__))
	for (key, key_type) in (("end", int), ("length", int), ("name", str), ("label", str)): # same as above, but additionally allows None
		if (not key in item):
			raise ValueError("item dict does not contain key '%s'" % key)
		if (not (isinstance(item[key], key_type) or item[key] == None)):
			raise TypeError("item[\"%s\"] must be type %s or None, not %s" % (key, key_type.__name__, type(item[key]).__name__))
	if (not isinstance(ins_mode, str)):
		raise TypeError("insertion mode must be type str, not %s" % type(ins_mode).__name__)
	if (not ins_mode in ("default", "start", "end")):
		raise ValueError("invalid insertion mode: '%s'" % ins_mode)

	if (ins_mode == "default"):
		for i in range(0, len(structure)):
			if (structure[i]["start"] > item["start"]):
				structure.insert(i, item)
				return structure[i]
	elif (ins_mode == "start"):
		for i in range(0, len(structure)):
			if (structure[i]["start"] > item["start"]):
				while (i > 1 and structure[i-1]["start"] == item["start"] and structure[i-1]["type"] == "variable"): i -= 1
				structure.insert(i, item)
				return structure[i]
	elif (ins_mode == "end"):
		for i in range(0, len(structure)):
			if (structure[i] == start_item):
				for j in range(i+1, len(structure)):
					if (structure[j]["start"] >= item["start"]):
						structure.insert(j, item)
						return structure[j]
	structure.append(item)
	return structure[-1]


# Determines and prints disasm structure stats
def print_structure_stats(structure):
	if (not isinstance(structure, list)):
		raise TypeError("structure must be type list, not %s" % type(structure).__name__)

	stats = OrderedDict()
	for item in structure:
		#key = "object" if item["type"].startswith("object") else "virtual padding" if item["type"].startswith("virtual padding") else "hint" if item["type"].startswith("hint") else "bad code" if item["type"].startswith("bad code") else item["type"] if item["type"] in ("module", "function", "branch", "variable") else "unknown"
		#key = "object" if item["type"].startswith("object") else "virtual padding" if item["type"].startswith("virtual padding") else "hint" if item["type"].startswith("hint") else "bad code" if item["type"].startswith("bad code") else item["type"] if item["type"] in ("module", "function", "branch", "variable", "reference") else "unknown"
		key = "object" if item["type"].startswith("object") else "module" if item["type"].startswith("module") else "virtual padding" if item["type"].startswith("virtual padding") else "hint" if item["type"].startswith("hint") else "bad code" if item["type"].startswith("bad code") else item["type"] if item["type"] in ("function", "branch", "variable", "reference") else "unknown"
		if (not key in stats):
			stats[key] = 0
		stats[key] += 1
	stats = [ "%s: %s" % (key, stats[key]) for key in stats.keys() ]
	logging.debug("Structure: %s, total: %d" % (str.join(", ", stats), len(structure)))



# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------



# ------------------------------------------------------------------------------
#                                                                              -
#  TODO: copied from legacy as is for now, needs to be revised thoroughly      -
#                                                                              -
# ------------------------------------------------------------------------------

# Generates a nice comment box
def generate_comment_box(content, width=80, spacing_left=2, spacing_right=2, spacing_top=1, spacing_bottom=1, comment_str=";", border_char="-"):

	# Sanity checks
	if (not (isinstance(content, str) or isinstance(content, tuple) or isinstance(content, list))):
		logging.error("Invalid content type: expected: str/tuple/list, got '%s'" % type(content).__name__)
		return None
	if (len(border_char) != 1):
		logging.error("Invalid border character length: expected: 1, got %d" % (len(border_char)))
		return None
	if (not width >= 0):
		logging.error("Invalid width: expected: >= 0, got %d" % width)
		return None
	if (not spacing_left >= 0):
		logging.error("Invalid left spacing: expected: >= 0, got %d" % spacing_left)
		return None
	if (not spacing_right >= 0):
		logging.error("Invalid right spacing: expected: >= 0, got %d" % spacing_right)
		return None
	if (not spacing_top >= 0):
		logging.error("Invalid top spacing: expected: >= 0, got %d" % spacing_top)
		return None
	if (not spacing_bottom >= 0):
		logging.error("Invalid bottom spacing: expected: >= 0, got %d" % spacing_bottom)
		return None

	# If content is string, wrap it into single paragraph
	if (isinstance(content, str)):
		content = [ content ]

	# Calculate and check inner width
	inner_width = width - len(comment_str) - spacing_left - spacing_right - len(border_char)
	if (not inner_width > 0):
		logging.error("Values for width, left spacing and right spacing result in invalid inner width: expected > 0, got %d" % inner_width)
		return None

	outer_str = comment_str + border_char * (width - len(comment_str))
	inner_tmp = comment_str + " " * spacing_left + "%-" + str(inner_width) + "s" + " " * spacing_right + border_char

	# Generate comment box
	result = []
	result.append(outer_str)
	for i in range(0, spacing_top):
		result.append(inner_tmp % "")
	for paragraph in content:
		if (len(paragraph) == 0):
			result.append(inner_tmp % "")
			continue
		for line in textwrap.wrap(paragraph, width=inner_width):
			result.append(inner_tmp % line)
	for i in range(0, spacing_bottom):
		result.append(inner_tmp % "")
	result.append(outer_str)
	return result


# Generates formatted disassembly, i.e. combine plain disassembly and disassembly structure to formatted disassembly
def generate_formatted_disassembly(object, globals_, fixrel):
	logging.info("Generating formatted disassembly of object %d:" % object["num"])

	# ------------------------------------------------------------------------------
	#  globals preparation                                                         -
	# ------------------------------------------------------------------------------

	# Create map of (object, offset) to globals
	# NOTE: we need globals for ALL objects, as references may point to other objects
	# NOTE: there may be multiple globals for the same (object, offset), e.g. MK1.EXE, object 1, THROW_SNOT
	#globals_map = { (item["object"], item["offset"]): item for item in globals_ }
	globals_map = {}
	for global_ in globals_:
		if (not (global_["object"], global_["offset"]) in globals_map):
			globals_map[(global_["object"], global_["offset"])] = []
		globals_map[(global_["object"], global_["offset"])].append(global_)

	# ------------------------------------------------------------------------------
	#  fixup / relocation preparation                                              -
	#  NOTE: currently only used to add fixup comments                             -
	# ------------------------------------------------------------------------------

	# Compile list of fixup records for current object, sort list by source
	# offset ascending (sort is important for mapping below!)
	logging.debug("Gathering fixup records for current object...")
	fixup_records = [ record for record in fixrel["record table"].values() if record["source object"] == object["num"] ]
	fixup_records.sort(key=lambda item: item["source offset 2"])
	logging.debug("Fixup records: total: %d, current object: %d" % (len(fixrel["record table"]), len(fixup_records)))

	# Create map of disassembly line offsets to fixup records (i.e. for each
	# disassembly line, get fixup records that apply to that line). A record
	# applies to a line if its source offset lies within the offset range of
	# the line (i.e. start_offset <= source offset < end_offset)
	logging.debug("Mapping disassembly offsets to fixup records...")
	fixup_map = {}
	record_index = 0
	for i in range(0, len(object["disasm plain"])):
		line = object["disasm plain"][i]
		if (record_index >= len(fixup_records)): # we're done early if there are no more records to process
			break
		asm = split_asm_line(line)
		if (asm == None):
			logging.warning("Invalid assembly line: line %d: '%s'" % (i+1, line))
			continue
		start_offset = asm["offset"]
		end_offset = asm["offset"] + len(asm["data"])
		records = []
		while (record_index < len(fixup_records) and fixup_records[record_index]["source offset 2"] >= start_offset and fixup_records[record_index]["source offset 2"] < end_offset):
			records.append(fixup_records[record_index])
			record_index += 1
		if (len(records) > 0):
			fixup_map[start_offset] = records

	# Print records that couldn't be mapped (if any); this can only happen
	# if there are records with source offsets outside of the disassembly's
	# offset range (which should not occur in real life)
	records_unmapped = 0
	while (record_index < len(fixup_records)):
		record = fixup_records[record_index]
		logging.warning("Unmapped record: source object: %d, source offset: 0x%x, target object: %d, target offset: 0x%x" % (record["source object"], record["source offset 2"], record["target object"], record["target offset"]))
		record_index += 1
		records_unmapped += 1

	# Print results
	records_mapped = 0
	for value in fixup_map.values():
		records_mapped += len(value)
	logging.debug("Mapped offsets: %d, mapped records: %d, unmapped records: %d" % (len(fixup_map), records_mapped, records_unmapped))

	# ------------------------------------------------------------------------------
	#  create formatted disassembly                                                -
	# ------------------------------------------------------------------------------

	# Process disassembly (for i in ...) and structure (while struct_index < ...)
	disassembly = []
	current_offset = 0
	end_offset = 0
	struct_index = 0
	# TESTING: module map
	module_map = OrderedDict()
	module_num = None
	for i in range(0, len(object["disasm plain"]) + 1):

		# All loop iterations except last one
		if (i < len(object["disasm plain"])):
			line = object["disasm plain"][i]
			asm = split_asm_line(line)
			if (asm == None):
				logging.warning("Invalid assembly line: line %d: '%s'" % (i+1, line))
			#elif (asm["type"] == "normal" or asm["type"] == "hex"):
			else:
				current_offset = asm["offset"]
				end_offset = asm["offset"] + len(asm["data"]) # need this for fixup record matching

		# Last loop iteration
		else:
			current_offset = object["virtual memory size"] if (object["virtual memory size"] > object["size"]) else object["size"]

		# Process structure items for current offset + those we may have missed in between last offset and current offset
		while (struct_index < len(object["disasm structure"]) and object["disasm structure"][struct_index]["start"] <= current_offset):
			item = object["disasm structure"][struct_index]

			pre = []
			if (item["start"] < current_offset):
				logging.warning("Misplaced item '%s' at offset 0x%x" % (item["name"], current_offset))
				pre = ["; misplaced item, should be at offset 0x%0x" % item["start"]]

			if (item["type"] == "object start"):
				disassembly += pre
				disassembly += generate_comment_box(content=["Object %d" % item["objnum"]], spacing_top=1, spacing_bottom=1)
			elif (item["type"] == "object end"):
				# TESTING: module map
				if (module_num != None and module_map[module_num][-1]["end"] == None):
					module_map[module_num][-1]["end"] = len(disassembly)
					module_num = None
				disassembly += [""] + pre
				disassembly += generate_comment_box(content=["End of object %d" % item["objnum"]], spacing_top=1, spacing_bottom=1)
			elif (item["type"] == "bad code start"):
				disassembly += pre
				#disassembly += generate_comment_box(content=["bad code (%s):" % item["subtype"]], spacing_top=0, spacing_bottom=0)
				disassembly += generate_comment_box(content=["Bad code %d (%s):" % (item["badnum"], item["badtype"])], width=50, spacing_top=0, spacing_bottom=0)
				for context in item["badcontext"]:
					disassembly.append(";%s" % (context[1:]))
				#disassembly += generate_comment_box(content=["padding data (%d bytes):" % item["padding"]], spacing_top=0, spacing_bottom=0)
				disassembly += generate_comment_box(content=["Padding data (%d bytes):" % item["badlength"]], width=50, spacing_top=0, spacing_bottom=0)
			elif (item["type"] == "bad code end"):
				disassembly += pre
				#disassembly += generate_comment_box(content=["end of padding / bad code"], spacing_top=0, spacing_bottom=0)
				disassembly += generate_comment_box(content=["End of bad code %d" % item["badnum"]], width=50, spacing_top=0, spacing_bottom=0)
			elif (item["type"] == "hint start"):
				#content = []
				#if (item["subtype"] == "data"):
				#	content += ["Hint %d (%s, %s, %d bytes):" % (item["hintnum"], item["subtype"], item["subtype2"], item["size"]), item["comment"]]
				disassembly += pre
				disassembly += generate_comment_box(content=[ "Hint %d (%s, %s, %d bytes):" % (item["hintnum"], item["hinttype"], item["hintmode"], item["hintlength"]) ] + ([ item["hintcomment"] ] if ("hintcomment" in item) else []), width=50, spacing_top=0, spacing_bottom=0)
			elif (item["type"] == "hint end"):
				disassembly += pre
				disassembly += generate_comment_box(content=["End of hint %d" % item["hintnum"]], width=50, spacing_top=0, spacing_bottom=0)
			elif (item["type"] == "virtual padding start"):
				disassembly += [""] + pre
				#disassembly += generate_comment_box(content=["End of actual data of object %d" % item["objnum"], "Start of padding data to match virtual size (%d bytes)" % item["size"]], spacing_top=1, spacing_bottom=1)
				disassembly += generate_comment_box(content=["End of actual data of object %d" % item["objnum"], "Start of virtual size padding data (%d bytes)" % item["size"]], spacing_top=1, spacing_bottom=1)
			elif (item["type"] == "virtual padding end"):
				# TESTING: module map
				if (module_num != None and module_map[module_num][-1]["end"] == None):
					module_map[module_num][-1]["end"] = len(disassembly)
					module_num = None
				disassembly += [""] + pre
				#disassembly += generate_comment_box(content=["End of padding data to match virtual size"], spacing_top=1, spacing_bottom=1)
				disassembly += generate_comment_box(content=["End of virtual size padding data"], spacing_top=1, spacing_bottom=1)
			#elif (item["type"] == "module"):
			#	# TESTING: module map
			#	if (module_num != None and module_map[module_num][-1]["end"] == None):
			#		module_map[module_num][-1]["end"] = len(disassembly)
			#	if (not item["modnum"] in module_map):
			#		module_map[item["modnum"]] = []
			#	module_map[item["modnum"]].append(OrderedDict([("start", len(disassembly)+1), ("end", None)]))
			#	module_num = item["modnum"]
			#	# ---
			#	disassembly += [""] + pre
			#	disassembly += generate_comment_box(content=["Module %d: %s" % (item["modnum"], item["name"])], spacing_top=1, spacing_bottom=1)
			# NOTE: module ends are important, e.g. MK1.EXE, object 1, 'Module 191: ini87386' ends at 0x3b2d5
			elif (item["type"] == "module start"):
				# TESTING: module map
				module_num = item["modnum"]
				if (not module_num in module_map):
					module_map[module_num] = []
				module_map[module_num].append(OrderedDict([("start", len(disassembly)+1), ("end", None)]))
				# ---
				disassembly += [""] + pre
				disassembly += generate_comment_box(content=["Module %d: %s" % (item["modnum"], item["name"])], spacing_top=1, spacing_bottom=1)
			elif (item["type"] == "module end"):
				disassembly += [""] + pre
				disassembly += generate_comment_box(content=["End of module %d (%s)" % (item["modnum"], item["name"])], spacing_top=1, spacing_bottom=1)
				# ---
				# TESTING: module map
				if (module_num != None and module_map[module_num][-1]["end"] == None):
					module_map[module_num][-1]["end"] = len(disassembly)
					module_num = None
			elif (item["type"] == "function"):
				disassembly += [""] + pre
				disassembly += generate_comment_box(content=["Function '%s'" % item["name"]], width=50, spacing_top=0, spacing_bottom=0)
				disassembly.append("%s:" % item["label"])
			elif (item["type"] == "branch"):
				disassembly += pre
				disassembly.append("%s:" % item["label"])
			elif (item["type"] == "reference"):
				disassembly += pre
				disassembly.append("%s:" % item["label"])
			elif (item["type"] == "variable"):
				disassembly += pre
				#if ("access sizes" in item):
				#	disassembly.append("%-50s ; %s: %s" % (item["label"] + ":", "access sizes" if (len(item["access sizes"]) > 1) else "size", str.join(", ", item["access sizes"])))
				#else:
				#	disassembly.append("%s:" % item["label"])
				disassembly.append("%s:" % item["label"])
			else:
				logging.error("[should-never-occur] Invalid structure type '%s'" % item["type"])

			# If item has access sizes, add corresponding comment
			if ("access sizes" in item):
				disassembly[-1] = "%-100s; %s: %s" % (disassembly[-1], "access sizes" if (len(item["access sizes"]) > 1) else "access size", str.join(", ", item["access sizes"]))

			struct_index += 1

		# Copy disassembly line (all but last loop iteration)
		if (i < len(object["disasm plain"])):

			# Check if fixups apply to current line -> replace target values with global label
			# NOTE: probably best to do this BEFORE call/jump analysis below; fixups are re-
			#       liable, whereas call/jump analysis is heuristic
			# NOTE: as there is no way to distinguish between fixup offsets and static numbers
			#       with the exact same value, we use re.findall() and bail out if there
			#       is more than one match for a target offset within the disassembly line
			# TODO: leading zeros are problematic, e.g. 'dd 0x00038c5a'; we should probably ditch
			#       leading zeros altogether (i.e. when generating 'db'/'dw'/'dd' statements)
			# TODO: merge this with adding comments for fixups (i.e. just move that stuff here)
			if (current_offset in fixup_map):
				for record in fixup_map[current_offset]:
					if (not "target offset" in record): # FIXME: SWS.EXE; probably fixups of different type, see 'main_fixup_relocation.py', line 276ff
						logging.warning("Skipping fixup record with missing 'target offset'")
						continue
					if (not (record["target object"], record["target offset"]) in globals_map):
						logging.warning("No global in map for fixup (target object %d, target offset 0x%x): %s" % (record["target object"], record["target offset"], line))
						continue
					matching_globals = globals_map[(record["target object"], record["target offset"])]
					if (not len(matching_globals) > 0):
						logging.warning("Empty list in global map for fixup (target object %d, target offset 0x%x): %s" % (record["target object"], record["target offset"], line))
						continue
					##match = re.search("(?:cs:|ds:|es:|fs:|gs:|ss:)?0x%x" % record["target offset"], asm["arguments"].strip())
					##match = re.search("(?:cs:|ds:|es:|fs:|gs:|ss:)?0x0*%x" % record["target offset"], asm["arguments"].strip())
					#match = re.search("0x0*%x" % record["target offset"], asm["arguments"].strip())
					#if (match == None):
					#	logging.warning("Failed to match fixup target offset 0x%x: %s" % (record["target offset"], line))
					#	continue
					#ofs_str = match.group(0)
					matches = re.findall("0x0*%x" % record["target offset"], asm["arguments"].strip())
					if (len(matches) == 0):
						logging.warning("Failed to match fixup target offset 0x%x: %s" % (record["target offset"], line))
						continue
					elif (len(matches) > 1):
						logging.warning("Multiple matches for fixup target offset 0x%x: %s" % (record["target offset"], line))
						continue
					ofs_str = matches[0]
					line = line.replace(ofs_str, "@obj%d:%s" % (matching_globals[0]["object"], matching_globals[0]["name"])) # FIXME: format just preliminary, need to investigate proper format
					if (len(matching_globals) == 1):
						continue
					line = "%-100s; aliases: %s" % (line, str.join(", ", [ item["name"] for item in matching_globals]))

			# Check if asm command is call or jump -> replace target with global label
			# NOTE: this intentionally only matches single constant address, e.g. 'je 0x39bd',
			#       but not 'call DWORD PTR ds:0x24850' (as the latter format is usually
			#       accompanied by a fixup)
			# NOTE: there might be multiple globals available for a given (object, offset),
			#       e.g. MK1.EXE, object 1, P_CONT + P_START @ 0xed84; simply use the first
			#       one and list the others in a comment
			if (asm["command"] == "call" or asm["command"].startswith("j")):
				match = re.match("^0x([0-9a-fA-F]+)$", asm["arguments"].strip())
				if (match != None):
					ofs_str = match.group(0) # entire string including '0x'
					ofs_val = int(match.group(1), 16)
					if ((object["num"], ofs_val) in globals_map):
						matching_globals = globals_map[((object["num"], ofs_val))]
						if (len(matching_globals) > 0):
							line = line.replace(ofs_str, matching_globals[0]["name"]) # use first global if multiple available
						else:
							logging.warning("Empty list in global map for (object %d, offset 0x%x): %s" % (object["num"], ofs_val, line))
						if (len(matching_globals) > 1):
							line = "%-100s; aliases: %s" % (line, str.join(", ", [ item["name"] for item in matching_globals]))
					else:
						logging.warning("No global in map for (object %d, offset 0x%x): %s" % (object["num"], ofs_val, line))
				# NOTE: this is fairly common and not an error (e.g. 'jmp ebx' won't match
				#       and we don't want it to)
				#else:
				#	logging.warning("Failed to match offset: %s" % line)

			# If fixups apply to current line, add corresponding comment
			#if (current_offset in fixup_map):
			#	for record in fixup_map[current_offset]:
			#		line += " ; fixup %d: source object: %d, source offset: 0x%x, target object: %d, target offset: 0x%x" % (record["num"], record["source object"], record["source offset 2"], record["target object"], record["target offset"])

			# If fixups apply to current line, add comment listing them
			# NOTE: this is very helpful for manual analysis of disassembly
			if (current_offset in fixup_map):
				fixup_comments = []
				for record in fixup_map[current_offset]:
					if (not "target offset" in record): # FIXME: SWS.EXE; probably fixups of different type, see 'main_fixup_relocation.py', line 276ff
						logging.warning("Skipping fixup record with missing 'target offset'")
						continue
					#fixup_comments.append("fixup: num: %d, source object: %d, source offset: 0x%x, target object: %d, target offset: 0x%x" % (record["num"], record["source object"], record["source offset 2"], record["target object"], record["target offset"]))
					fixup_comments.append("fixup: num: %d, src obj: %d, src ofs: 0x%x, dst obj: %d, dst ofs: 0x%x" % (record["num"], record["source object"], record["source offset 2"], record["target object"], record["target offset"]))
				line = "%-100s; %s" % (line, str.join("; ", fixup_comments))

			# Append line to disassembly
			#line = line.replace(":\t", ":  ") # tab after '<offset>:'
			#line = line.replace(" \t", "  ")  # tab after hex data
			disassembly.append(line)

	# Store results
	logging.debug("Size of formatted disassembly: %d lines, %d bytes" % (len(disassembly), len(str.join(os.linesep, disassembly))))
	object["disasm formatted"] = disassembly

	# TESTING: module map
	object["module map"] = module_map


# ----------------- preprocessing --------------------


# Preprocess objects:
# - accumulate object data over pages/segments
# - determine size of actual data
# - add padding data for virtual size
# - determine object type
# - add object hints
# - sort object hints by number
# - add flag for automatic data object
# - sort objects by number
# NOTE:
# Objects don't necessarily have pages, e.g. Syndicate executables have objects without pages
# NOTE:
# object["virtual memory size"]: virtual object size (if > actual data size, virtual padding data will be added)
# object["actual data size"]:    size of actual data (i.e. without virtual padding)
# object["size"]:                size of all data (i.e. actual data + virtual padding)
# object["data"]:                all data (i.e. actual data + virtual padding)
def preprocess_objects(wdump):
	logging.debug("Preprocessing objects...")

	if (not "object table" in wdump):
		logging.warning("No object table present in wdump data")
		return []

	objects = []
	ado_num = dict_path_value(wdump, "linear exe header (os/2 v2.x) - le", "data", "object # for automatic data object")
	for object in wdump["object table"]["data"].values():
		object_size = 0
		object_data = b''
		if ("pages" in object):
			for page in object["pages"].values():
				page_size = 0
				page_data = b''
				for segment in page["segments"].values():
					segment_size = len(segment["data"])
					page_size += segment_size
					page_data += segment["data"]
				if (len(page_data) != page_size):
					logging.warning("len(page_data) != page_size")
				object_size += page_size
				object_data += page_data
		if (len(object_data) != object_size):
			logging.warning("len(object_data) != object_size")
		if (len(object_data) < object["virtual memory size"]):
			object_data += bytes(object["virtual memory size"] - len(object_data))
		#object_type = "code" if ("executable" in object["flags"].lower()) else "data"
		object_type = "code" if ("executable" in object["flags"]) else "data"
		object_hints = []
		if ("object hints" in wdump and object["num"] in wdump["object hints"]["data"]):
			for entry in wdump["object hints"]["data"][object["num"]]["entries"].values():
				object_hints.append(OrderedDict([(key, entry[key]) for key in entry.keys()]))
			##object_hints.sort(key=lambda item: item["offset"])
			#object_hints.sort(key=lambda item: item["start"]) # NOTE: unsorted is better for building data map, leaving this here for future reference
			object_hints.sort(key=lambda item: item["num"])
		object_ado = None if (ado_num == None or object_type != "data") else True if (object["num"] == ado_num) else False
		#objects.append(OrderedDict([(key, object[key]) for key in object.keys() if (key != "pages")] + ([("automatic data object", object_ado)] if (object_ado != None) else []) + [("actual data size", object_size), ("size", len(object_data)), ("data", object_data), ("type", object_type), ("hints", object_hints), ("data map", [])] + ([("bad code", [])] if (object_type == "code") else []) + [("disasm structure", []), ("disasm plain", []), ("disasm formatted", [])])) # https://stackoverflow.com/a/32895702
		objects.append(OrderedDict([(key, object[key]) for key in object.keys() if (key != "pages")] + ([("automatic data object", object_ado)] if (object_ado != None) else []) + [("actual data size", object_size), ("size", len(object_data)), ("data", object_data), ("type", object_type), ("hints", object_hints), ("data map", []), ("bad code", []), ("disasm structure", []), ("disasm plain", []), ("disasm formatted", [])])) # https://stackoverflow.com/a/32895702

	objects.sort(key=lambda item: item["num"])

	logging.debug("Preprocessed %d objects" % len(objects))
	return objects


# Preprocess modules:
# - accumulate modules over subsections
# - accumulate address info over subsections and add to modules -> module["offsets"]
# - sort offsets (address info) by parent object (segment), offset
# - sort modules by number
# NOTE:
# Temporarily using OrderedDict for modules to facilitate adding address info,
# reduced to list near end of this code block
def preprocess_modules(wdump):
	logging.debug("Preprocessing modules...")

	if (not "module info" in wdump):
		logging.warning("No module info present in wdump data")
		return []

	modules = OrderedDict() # only temporary, reduced to list near end of function

	for subsec in wdump["module info"]["data"].values():
		for module in subsec["data"].values():
			modules[module["num"]] = OrderedDict([(key, module[key]) for key in module.keys() if (not key in ("locals", "types", "lines"))] + [("offsets", [])])

	for subsec in wdump["addr info"]["data"].values():
		for segment in subsec["data"]:
			for entry in segment["entries"].values():
				if (not entry["module"] in modules):
					logging.error("Error: invalid module index: %d" % entry["module"])
					continue
				#modules[entry["module"]]["offsets"].append(OrderedDict([("segment", segment["segment"]), ("offset", entry["offset"]), ("size", entry["size"])]))
				modules[entry["module"]]["offsets"].append(OrderedDict([("object", segment["segment"]), ("offset", entry["offset"]), ("size", entry["size"])]))

	for module in modules.values():
		#module["offsets"].sort(key=lambda item: (item["segment"], item["offset"]))
		module["offsets"].sort(key=lambda item: (item["object"], item["offset"]))

	modules = list(modules.values())
	modules.sort(key=lambda item: item["num"])

	logging.debug("Preprocessed %d modules" % len(modules))
	return modules


# Preprocess globals:
# - accumulate globals over subsections
# - add source -> all globals at this point come from debug info
# - sort globals by parent object (segment), offset
def preprocess_globals(wdump):
	logging.debug("Preprocessing globals...")

	if (not "global info" in wdump):
		logging.warning("No global info present in wdump data")
		return []

	globals_ = []
	for subsec in wdump["global info"]["data"].values():
		for global_ in subsec["data"]:
			#globals_.append(OrderedDict([(key, global_[key]) for key in global_.keys()]))
			globals_.append(OrderedDict([(key if (key != "segment") else "object", global_[key]) for key in global_.keys()] + [("source", "debug info")]))

	#globals_.sort(key=lambda item: (item["segment"], item["offset"]))
	globals_.sort(key=lambda item: (item["object"], item["offset"]))

	logging.debug("Preprocessed %d globals" % len(globals_))
	return globals_


# Preprocess fixups:
# - strip data down to what we actually need
# - sort fixups by source object, source offset
def preprocess_fixups(fixrel):
	logging.debug("Preprocessing fixups...")

	if (not "record table" in fixrel):
		logging.warning("No record table present in fixup/relocation data")
		return []

	fixups = []
	for record in fixrel["record table"].values():
		if not "target offset" in record: # FIXME: SWS.EXE; probably fixups of different type, see 'main_fixup_relocation.py', line 276ff
			logging.warning("skipping fixup record with missing 'target offset'")
			continue
		fixups.append(OrderedDict([("num", record["num"]), ("source object", record["source object"]), ("source offset", record["source offset 2"]), ("target object", record["target object"]), ("target offset", record["target offset"])]))

	fixups.sort(key=lambda item: (item["source object"], item["source offset"]))

	logging.debug("Preprocessed %d fixups" % len(fixups))
	return fixups


# ----------------- miscellaneous --------------------


# Analyze references in fixup/relocation data and add corresponding globals
# NOTE: adds directly to globals_, does not return anything
def analyze_fixups_add_globals(objects, globals_, fixups):
	# Analyze references in fixup/relocation data and add corresponding globals
	#if ("record table" in fixup):
	#	logging.debug("Analyzing references in fixup/relocation data...")
	#	added_globals = 0
	#	for object in disasm["objects"]:
	#		#known_offsets = { item["offset"]: None for item in disasm["globals"] if (item["segment"] == object["num"]) }
	#		known_offsets = { item["offset"]: None for item in disasm["globals"] if (item["object"] == object["num"]) }
	#		offsets_before = len(known_offsets)
	#		fixup_records = [ item for item in fixup["record table"].values() if (item["target object"] == object["num"]) ]
	#		for record in fixup_records:
	#			if (record["target offset"] in known_offsets):
	#				continue
	#			offset = record["target offset"]
	#			#disasm["globals"].append(OrderedDict([("name", None), ("module", None), ("segment", object["num"]), ("offset", offset), ("type", object["type"]), ("source", "fixup data")]))
	#			disasm["globals"].append(OrderedDict([("name", None), ("module", None), ("object", object["num"]), ("offset", offset), ("type", object["type"]), ("source", "fixup data")]))
	#			added_globals += 1
	#			known_offsets[offset] = None
	#		offsets_after = len(known_offsets)
	#		offsets_added = offsets_after - offsets_before
	#		logging.debug("Object %d: offsets before: %d, offsets added: %d, offsets after: %d" % (object["num"], offsets_before, offsets_added, offsets_after))
	#	#disasm["globals"].sort(key=lambda item: (item["segment"], item["offset"]))
	#	disasm["globals"].sort(key=lambda item: (item["object"], item["offset"]))
	#	logging.debug("Added %d globals for fixup/relocation references" % added_globals)

	# Analyze references in fixup/relocation data and add corresponding globals
	# NOTE: simplified variant, using tuple as key to hash known items
	#if ("record table" in fixup):
	#	logging.debug("Analyzing references in fixup/relocation data...")
	#	added_globals = 0
	#	object_types = { item["num"]: item["type"] for item in disasm["objects"] }
	#	#known_globals = { (item["segment"], item["offset"]): item for item in disasm["globals"] }
	#	known_globals = { (item["object"], item["offset"]): item for item in disasm["globals"] }
	#	for record in fixup["record table"].values():
	#		if ((record["target object"], record["target offset"]) in known_globals):
	#			continue
	#		disasm["globals"].append(OrderedDict([("name", None), ("module", None), ("object", record["target object"]), ("offset", record["target offset"]), ("type", object_types[record["target object"]]), ("source", "fixup data")]))
	#		known_globals[(record["target object"], record["target offset"])] = disasm["globals"][-1]
	#		added_globals += 1
	#	disasm["globals"].sort(key=lambda item: (item["object"], item["offset"]))
	#	logging.debug("Added %d globals for fixup/relocation references" % added_globals)

	# Analyze references in fixup/relocation data and add corresponding globals
	# NOTE: same as above, but using preprocessed fixups
	logging.debug("Analyzing fixup references...")
	added_globals = 0
	obj_num_to_type = { item["num"]: item["type"] for item in objects }
	#known_globals = { (item["segment"], item["offset"]): item for item in globals_ }
	known_globals = { (item["object"], item["offset"]): item for item in globals_ }
	for fixup in fixups:
		if ((fixup["target object"], fixup["target offset"]) in known_globals):
			continue
		globals_.append(OrderedDict([("name", None), ("module", None), ("object", fixup["target object"]), ("offset", fixup["target offset"]), ("type", obj_num_to_type[fixup["target object"]]), ("source", "fixup data")]))
		known_globals[(fixup["target object"], fixup["target offset"])] = globals_[-1]
		added_globals += 1
	globals_.sort(key=lambda item: (item["object"], item["offset"]))
	logging.debug("Added %d globals for fixup references (%d globals total)" % (added_globals, len(globals_)))


# ------------------- data maps ----------------------


# Object data maps:
# - list of dicts
# - each item has: start offset, end offset, type (data/code), mode
# - map starts with a single initial item covering all of the object's data
#   (i.e. start = 0, end = object size, type = object type, mode = default)
# - insert function inserts new items by splicing them into existing ones
#   (in other words, the big single initial item is gradually sliced into
#   smaller pieces with/by each newly inserted item)
#
# NOTE:
# Contrary to the name, a data map itself is NOT a map (i.e. dict), but in-
# stead a list of dicts describing the layout of an object's binary data.
# The list items are processed sequentially when disassembling (see below)


# Custom exception raised by insert_data_map_item()
class DataMapInsertError(Exception):
	pass


# Insert (i.e. splice) new item into data map (item must have start offset,
# end offset, type (data/code) and mode)

#def insert_data_map_item(data_map, ins_item):
#
#	# Locate splice position and splice item (existing item at splice position)
#	splice_pos = None
#	splice_item = None
#	for i, item in enumerate(data_map):
#		if (ins_item["start"] >= item["start"] and ins_item["end"] <= item["end"]):
#			splice_pos = i
#			splice_item = item
#			break
#	if (splice_pos == None or splice_item == None):
#		raise DataMapInsertError("Failed to locate splice position/item for insert item")
#	if (splice_item["start"] == ins_item["start"] and splice_item["end"] == ins_item["end"]):
#		raise DataMapInsertError("Splice item has same range as insert item")
#	if (splice_item["type"] == ins_item["type"] and splice_item["mode"] == ins_item["mode"]):
#		raise DataMapInsertError("Splice item has same type/mode as insert item")
#
#	# Insert item by replacing splice item with 3 new items (splice_item -> splice_item_head + ins_item + splice_item_tail)
#	splice_item = data_map.pop(splice_pos)
#	data_map.insert(splice_pos, OrderedDict([("start", splice_item["start"]), ("end", ins_item["start"]), ("type", splice_item["type"]), ("mode", splice_item["mode"])]))
#	data_map.insert(splice_pos + 1, OrderedDict([("start", ins_item["start"]), ("end", ins_item["end"]), ("type", ins_item["type"]), ("mode", ins_item["mode"])]))
#	data_map.insert(splice_pos + 2, OrderedDict([("start", ins_item["end"]), ("end", splice_item["end"]), ("type", splice_item["type"]), ("mode", splice_item["mode"])]))

# NOTE:
# For simplicity, this implementation only handles/allows gradual down-
# sizing/splitting of existing ranges. Fancy things like merging ranges
# are not supported. Should be fine like this for our use case, though
# TODO:
# - remove support for immutable ranges; instead, add support for extending,
#   replacing and merging ranges -> find splice start + splice end, pop items
#   from start to end, splice insert item into start and end, drop everything
#   in between
#   -> when this is done, move processing of hints so that hint items are
#      added to the data map after everything else;  by doing this, hints take
#      precedence because they are the very last change applied to the data
#      map
# TODO:
# - should we extend this to support merging, extending etc. of ranges? we should
#   probably at least have a final optimization run that merges adjacent ranges
#   with identical properties
#def insert_data_map_item(data_map, ins_item):
#
#	# Sanity checks
#	if (not isinstance(data_map, list)):
#		raise TypeError("data map must be type list, not %s" % type(data_map).__name__)
#	if (not isinstance(ins_item, dict)):
#		raise TypeError("insert item must be type dict, not %s" % type(ins_item).__name__)
#	for (key, key_type) in (("start", int), ("end", int), ("type", str), ("mode", str), ("source", str), ("immutable", bool)):
#		if (not key in ins_item):
#			raise ValueError("insert item dict does not contain key '%s'" % key)
#		if (not isinstance(ins_item[key], key_type)):
#			raise TypeError("ins_item[\"%s\"] must be type %s or None, not %s" % (key, key_type.__name__, type(ins_item[key]).__name__))
#	# NOTE: start == end happens frequently (e.g. MK1.EXE, object 1, 'THROW_SNOT:'); not a problem; handled below
#	#if (ins_item["end"] <= ins_item["start"]):
#	#	raise ValueError("insert item has invalid range (end <= start): start: 0x%s, end: 0x%s" % (ins_item["start"], ins_item["end"]))
#	if (ins_item["end"] < ins_item["start"]):
#		raise ValueError("insert item has invalid range (end < start): start: 0x%s, end: 0x%s" % (ins_item["start"], ins_item["end"]))
#	# NOTE: these are checked in generate_data_disassembly(), better not duplicate here
#	#if (not ins_item["type"] in ("code", "data")):
#	#	raise ValueError("invalid ins_item[\"type\"]: '%s'" % ins_item["type"])
#	#if (not ins_item["mode"] in ("default", "auto-strings", "strings", "string", "bytes", "words", "dwords", "fwords", "qwords")):
#	#	raise ValueError("invalid ins_item[\"mode\"]: '%s'" % ins_item["mode"])
#
#	# Trivial case: start == end -> range == 0 -> nothing to do
#	if (ins_item["end"] == ins_item["start"]):
#		return
#
#	# Locate splice position and splice item (i.e. existing item at splice position)
#	splice_pos = None
#	splice_item = None
#	for i, item in enumerate(data_map):
#		if (ins_item["start"] >= item["start"] and ins_item["end"] <= item["end"]):
#			splice_pos = i
#			splice_item = item
#			break
#
#	# No splice position/item found
#	if (splice_pos == None or splice_item == None):
#		#raise DataMapInsertError("Failed to locate splice position/item for insert item")
#		raise DataMapInsertError("failed to locate splice position/item")
#
#	# Check if item to be inserted has same properties as splice item
#	#if (splice_item["start"] == ins_item["start"] and splice_item["end"] == ins_item["end"] and splice_item["type"] == ins_item["type"] and splice_item["mode"] == ins_item["mode"]):
#	#	raise DataMapInsertError("Splice item has same start, end, type and mode as insert item")
#	if (splice_item == ins_item): # Python supports comparing dicts directly!
#		#raise DataMapInsertError("Splice item has exact same properties as insert item")
#		#raise DataMapInsertError("Splice item has exact same properties")
#		return # not an error, as item with exact same properties is already present
#
#	# Prevent splicing into of immutable items
#	if (splice_item["immutable"] == True):
#		raise DataMapInsertError("refusing to splice into immutable item")
#
#	# Insert item by replacing splice item with 3 new items: splice_item -> splice_item_head + ins_item + splice_item_tail
#	splice_item = data_map.pop(splice_pos)
#	if (splice_item["start"] != ins_item["start"]):
#		data_map.insert(splice_pos, OrderedDict([("start", splice_item["start"]), ("end", ins_item["start"]), ("type", splice_item["type"]), ("mode", splice_item["mode"]), ("source", splice_item["source"]), ("immutable", splice_item["immutable"])]))
#		splice_pos += 1
#	if (ins_item["start"] != ins_item["end"]):
#		data_map.insert(splice_pos, OrderedDict([("start", ins_item["start"]), ("end", ins_item["end"]), ("type", ins_item["type"]), ("mode", ins_item["mode"]), ("source", ins_item["source"]), ("immutable", ins_item["immutable"])]))
#		splice_pos += 1
#	if (ins_item["end"] != splice_item["end"]):
#		data_map.insert(splice_pos, OrderedDict([("start", ins_item["end"]), ("end", splice_item["end"]), ("type", splice_item["type"]), ("mode", splice_item["mode"]), ("source", splice_item["source"]), ("immutable", splice_item["immutable"])]))

# NOTE:
# Rewrite supporting merging and extending ranges (by splicing into / replacing
# multiple existing items instead of just one). Created this to replace former
# method of using 'immutable' items
def insert_data_map_item(data_map, ins_item):

	# Sanity checks
	if (not isinstance(data_map, list)):
		raise TypeError("data map must be type list, not %s" % type(data_map).__name__)
	if (not isinstance(ins_item, dict)):
		raise TypeError("insert item must be type dict, not %s" % type(ins_item).__name__)
	for (key, key_type) in (("start", int), ("end", int), ("type", str), ("mode", str), ("source", str)):
		if (not key in ins_item):
			raise ValueError("insert item dict does not contain key '%s'" % key)
		if (not isinstance(ins_item[key], key_type)):
			raise TypeError("ins_item[\"%s\"] must be type %s or None, not %s" % (key, key_type.__name__, type(ins_item[key]).__name__))
	if (ins_item["end"] < ins_item["start"]):
		raise ValueError("insert item has invalid range (end < start): start: 0x%s, end: 0x%s" % (ins_item["start"], ins_item["end"]))

	# If start offset == end offset, the insert item can be ignored as it would
	# not add anything to the data map (items like this are quite common, e.g.
	# MK1.EXE, object 1, 'THROW_SNOT:')
	if (ins_item["start"] == ins_item["end"]):
		return

	# Locate splice start index/item within data map
	# NOTE: iterating list indices in reversed order is important here
	start_index = None
	start_item = None
	for i in reversed(range(0, len(data_map))):
		if (ins_item["start"] >= data_map[i]["start"]):
			start_index = i
			start_item = data_map[i]
			break
	if (start_index == None or start_item == None):
		raise DataMapInsertError("failed to locate splice start index/item")

	# Locate splice end index/item within data map
	# NOTE: end index/item may ultimately be the same as start index/item
	end_index = None
	end_item = None
	for i in range(start_index, len(data_map)):
		if (ins_item["end"] <= data_map[i]["end"]):
			end_index = i
			end_item = data_map[i]
			break
	if (end_index == None or end_item == None):
		raise DataMapInsertError("failed to locate splice end index/item")

	# If splice start index/item == splice end index/item and that item has the
	# exact same properties as the insert item, the insert item can be ignored
	# as it would not add anything to the data map
	# NOTE: Python supports comparing dicts using '==' operator
	if ((start_index == end_index) and (start_item == end_item == ins_item)):
		return

	# Remove items from start to end from data map
	# NOTE: +1 is required as slicing excludes end index in Python
	del data_map[start_index:end_index+1]

	# Splice insert item into data map by replacing the removed items with 3 new
	# items: start item head + insert item + end item tail
	# NOTE: insertion order reversed to allow start_index to remain constant
	if (end_item["end"] > ins_item["end"]): # end item tail
		data_map.insert(start_index, OrderedDict([("start", ins_item["end"]), ("end", end_item["end"]), ("type", end_item["type"]), ("mode", end_item["mode"]), ("source", end_item["source"])]))
	data_map.insert(start_index, OrderedDict([("start", ins_item["start"]), ("end", ins_item["end"]), ("type", ins_item["type"]), ("mode", ins_item["mode"]), ("source", ins_item["source"])]))
	if (start_item["start"] < ins_item["start"]): # start item head
		data_map.insert(start_index, OrderedDict([("start", start_item["start"]), ("end", ins_item["start"]), ("type", start_item["type"]), ("mode", start_item["mode"]), ("source", start_item["source"])]))


# Check data map consistency
# NOTE: created for debugging purposes only
def check_data_map_consistency(object_num, data_map):
	issues = 0

	# Check if data map is empty
	if (len(data_map) == 0):
		logging.warning("Data map is empty")
		issues += 1

	# Check if first item starts at 0x0
	if ((len(data_map) > 0) and (data_map[0]["start"] != 0x0)):
		logging.warning("First item does not start at 0x0: data_map[0][\"start\"] == 0x%x" % data_map[0]["start"])
		issues += 1

	# Check if there are 'holes' in between items
	for i in range(0, len(data_map)-1):
		if (data_map[i]["end"] != data_map[i+1]["start"]):
			logging.warning("Hole in between items %d and %d: data_map[%d][\"end\"] == 0x%x  !=  data_map[%d][\"start\"] == 0x%x" % (i, i+1, i, data_map[i]["end"], i+1, data_map[i+1]["start"]))
			issues += 1

	# Print results
	if (issues > 0):
		logging.error("Consistency check revealed %d issues" % issues)
	else:
		logging.debug("Data map of object %d is consistent" % object_num)



# --------------------- main -------------------------


# Disassemble objects
def disassemble_objects(wdump, fixrel, objdump_exec, outfile_template):
	logging.info("")
	logging.info("Disassembling objects:")

	# Storage for results
	disasm = OrderedDict([("objects", []), ("modules", []), ("globals", []), ("fixups", [])])


	# Preprocess objects, modules, globals and fixups (i.e. extract from wdump/
	# fixrel data, accumulate and convert to format required for further steps)
	# TODO: unsure if 'preprocess' is a good term for this; convert, generate, format, ...?
	logging.info("")
	logging.info("Preprocessing objects, modules, globals and fixups:")
	disasm["objects"] = preprocess_objects(wdump)
	disasm["modules"] = preprocess_modules(wdump)
	disasm["globals"] = preprocess_globals(wdump)
	disasm["fixups"] = preprocess_fixups(fixrel)


	# Analyze references in fixup/relocation data and add corresponding globals
	# TODO: not really sure if this is a good position
	# TODO: does currently not belong to any group of actions; could make this part of preprocessing
	logging.debug("")
	analyze_fixups_add_globals(disasm["objects"], disasm["globals"], disasm["fixups"])


	# Build data maps for code objects
	logging.info("")
	logging.info("Building data maps for code objects:")
	#for object in disasm["objects"]:
	for object in [ item for item in disasm["objects"] if (item["type"] == "code") ]:
		logging.debug("Building data map for object %d..." % object["num"])

		# Initialize data map with object item spanning accross all data
		object["data map"] = [ OrderedDict([("start", 0), ("end", object["size"]), ("type", object["type"]), ("mode", "default"), ("source", "object")]) ]

		# Modules
		for module in disasm["modules"]:
			for offset in [ item for item in module["offsets"] if (item["object"] == object["num"]) ]:
				try:
					insert_data_map_item(object["data map"], OrderedDict([("start", offset["offset"]), ("end", offset["offset"] + offset["size"]), ("type", object["type"]), ("mode", "default"), ("source", "module")]))
				except DataMapInsertError as dmie:
					logging.warning("%s: module: num: %d, start: 0x%x, end: 0x%x, length: 0x%x (%d), name: %s" % (str(dmie), module["num"], offset["offset"], offset["offset"] + offset["size"], offset["size"], offset["size"], module["name"]))

		# Globals
		# NOTE:
		# This adds data map items for globals. The difficulty here is that globals
		# only come with an offset (i.e. start), but not with an end or size. Thus,
		# ends/sizes are calculated by sorting all globals by offset ascending and
		# then calculating the distance between one global and the next one. Also,
		# module boundaries need to be considered as globals cannot extend beyond
		# the end of the module they belong to
		# NOTE:
		# We only consider globals supplied by debug info here; globals from fixups
		# wouldn't help or even hurt as they can point anywhere within the code, i.e.
		# they are not bound to disassembly line offsets (globals from debug info
		# on the other hand should be)
		module_bounds = {}
		for module in disasm["modules"]:
			for offset in [ item for item in module["offsets"] if (item["object"] == object["num"]) ]:
				if (not module["num"] in module_bounds):
					module_bounds[module["num"]] = []
				module_bounds[module["num"]].append(OrderedDict([("start", offset["offset"]), ("end", offset["offset"] + offset["size"])]))
			if (module["num"] in module_bounds):
				module_bounds[module["num"]].sort(key=lambda item: (item["start"], item["end"]), reverse=True) # reverse sort order is important, won't work otherwise!

		object_globals = [ item for item in disasm["globals"] if (item["object"] == object["num"] and item["source"] == "debug info") ]
		object_globals.sort(key=lambda item: item["offset"])
		for i in range(0, len(object_globals)):
			current_global = object_globals[i]

			if (i < len(object_globals)-1): # all items except last one
				next_global = object_globals[i+1]
				current_global["size"] = next_global["offset"] - current_global["offset"]
			else: # last item
				current_global["size"] = object["size"] - current_global["offset"]

			if (not current_global["module"] in module_bounds): # this could probably happen if there is no debug info regarding modules
				continue

			bounds = module_bounds[current_global["module"]]
			for bound in bounds:
				if (current_global["offset"] < bound["start"]): # check if global lies within module (only works if bounds are sorted correctly!)
					continue
				if (current_global["offset"] + current_global["size"] > bound["end"]): # check if global size exceeds module end boundary
					new_size = bound["end"] - current_global["offset"]
					#logging.debug("Resizing global to module boundary: name: %s: start: 0x%x, end: 0x%x, length: 0x%x (%d) -> start: 0x%x, end: 0x%x, length: 0x%x (%d)" % (current_global["name"], current_global["offset"], current_global["offset"] + current_global["size"], current_global["size"], current_global["size"], current_global["offset"], current_global["offset"] + new_size, new_size, new_size))
					current_global["size"] = new_size
				break

		for global_ in object_globals:
			try:
				insert_data_map_item(object["data map"], OrderedDict([("start", global_["offset"]), ("end", global_["offset"] + global_["size"]), ("type", global_["type"]), ("mode", "default"), ("source", "global")]))
			except DataMapInsertError as dmie:
				logging.warning("%s: global: name: %s, start: 0x%x, end: 0x%x, length: 0x%x (%d), type: %s" % (str(dmie), global_["name"], global_["offset"], global_["offset"] + global_["size"], global_["size"], global_["size"], global_["type"]))

		# Hints
		# NOTE:
		# Hints need to be added last so they can take precedence over existing items
		for hint in object["hints"]:
			# TODO:
			# Currently, object hints are not sorted/ordered (they were before, we de-
			# cided against it for now). If they were in order, we could optimize loop
			#   for i in range(0, len(object["data map"]))
			# to:
			#   for i in range(last_splice_pos, len(object["data map"]))

			#splice_pos = None
			#for i in range(0, len(object["data map"])):
			#	item = object["data map"][i]
			#	if (hint["start"] >= item["start"] and hint["end"] <= item["end"]):
			#		splice_pos = i
			#		break
			#if (splice_pos == None):
			#	logging.warning("Failed to locate splice position for hint %d: start: 0x%x, end: 0x%x, length: 0x%x (%d), type: %s, mode: %s" % (hint["num"], hint["start"], hint["end"], hint["length"], hint["length"], hint["type"], hint["mode"]))
			#	continue
			#item = object["data map"][splice_pos]
			#if (item["start"] == hint["start"] and item["end"] == hint["end"]):
			#	logging.warning("Splice item has same range as hint %d: start: 0x%x, end: 0x%x, length: 0x%x (%d), type: %s, mode: %s" % (hint["num"], hint["start"], hint["end"], hint["length"], hint["length"], hint["type"], hint["mode"]))
			#	continue
			#if (item["type"] == hint["type"] and item["mode"] == hint["mode"]):
			#	logging.warning("Splice item has same type/mode as hint %d: start: 0x%x, end: 0x%x, length: 0x%x (%d), type: %s, mode: %s" % (hint["num"], hint["start"], hint["end"], hint["length"], hint["length"], hint["type"], hint["mode"]))
			#	continue
			#item = object["data map"].pop(splice_pos)
			#object["data map"].insert(splice_pos, OrderedDict([("start", item["start"]), ("end", hint["start"]), ("type", item["type"]), ("mode", item["mode"])]))
			#object["data map"].insert(splice_pos + 1, OrderedDict([("start", hint["start"]), ("end", hint["end"]), ("type", hint["type"]), ("mode", hint["mode"])]))
			#object["data map"].insert(splice_pos + 2, OrderedDict([("start", hint["end"]), ("end", item["end"]), ("type", item["type"]), ("mode", item["mode"])]))

			#if (hint["start"] > object["size"]):
			#	logging.warning("Hint range is out of object bounds: num: %d, start: 0x%x, end: 0x%x, length: 0x%x (%d), type: %s, mode: %s" % (hint["num"], hint["start"], hint["end"], hint["length"], hint["length"], hint["type"], hint["mode"]))
			#	continue
			if (hint["mode"] == "comment"): # skip comment-only hints (no use for data map)
				continue
			try:
				insert_data_map_item(object["data map"], OrderedDict([("start", hint["start"]), ("end", hint["end"]), ("type", hint["type"]), ("mode", hint["mode"]), ("source", "hint")]))
			except DataMapInsertError as dmie:
				#logging.warning("%s: hint %d: start: 0x%x, end: 0x%x, length: 0x%x (%d), type: %s, mode: %s" % (str(dmie), hint["num"], hint["start"], hint["end"], hint["length"], hint["length"], hint["type"], hint["mode"]))
				logging.warning("%s: hint: num: %d, start: 0x%x, end: 0x%x, length: 0x%x (%d), type: %s, mode: %s" % (str(dmie), hint["num"], hint["start"], hint["end"], hint["length"], hint["length"], hint["type"], hint["mode"]))


		logging.debug("Data map for object %d has %d entries" % (object["num"], len(object["data map"])))

		logging.debug("Checking consistency of data map for object %d..." % object["num"])
		check_data_map_consistency(object["num"], object["data map"])


	# TESTING: Extend data maps of data objects by making use of fixup/relocation data
	#          -> we know that memory references are 32 bit, so we can decode references in data objects as dwords
	##if ("record table" in fixup):
	##	logging.debug("Adding to data maps of data objects...")
	##	for object in [ item for item in disasm["objects"] if (item["type"] == "data") ]:
	##		fixup_records = [ item for item in fixup["record table"].values() if (item["source object"] == object["num"]) ]
	##		fixup_records.sort(key=lambda item: item["source offset 2"])
	##		for record in fixup_records:
	##			try:
	##				insert_data_map_item(object["data map"], OrderedDict([("start", record["source offset 2"]), ("end", record["source offset 2"] + 4), ("type", "data"), ("mode", "dwords")]))
	##			except DataMapInsertError as dmie:
	##				logging.warning("%s: fixup record %d: source object: %d, source offset: 0x%x, target object: %d, target offset: 0x%x" % (str(dmie), record["num"], record["source object"], record["source offset 2"], record["target object"], record["target offset"]))
	##	logging.debug("Map for object %d has %d entries" % (object["num"], len(object["data map"])))
	#logging.debug("Extending data maps of data objects using fixups...")
	#for object in [ item for item in disasm["objects"] if (item["type"] == "data") ]:
	#	for fixup in [ item for item in disasm["fixups"] if (item["source object"] == object["num"]) ]:
	#		try:
	#			insert_data_map_item(object["data map"], OrderedDict([("start", fixup["source offset"]), ("end", fixup["source offset"] + 4), ("type", "data"), ("mode", "dwords")]))
	#		except DataMapInsertError as dmie:
	#			#logging.warning("%s: fixup %d: source object: %d, source offset: 0x%x, target object: %d, target offset: 0x%x" % (str(dmie), fixup["num"], fixup["source object"], fixup["source offset"], fixup["target object"], fixup["target offset"]))
	#			logging.warning("%s fixup: num: %d, source object: %d, source offset: 0x%x, target object: %d, target offset: 0x%x" % (str(dmie), fixup["num"], fixup["source object"], fixup["source offset"], fixup["target object"], fixup["target offset"]))
	#logging.debug("Map for object %d has %d entries" % (object["num"], len(object["data map"])))


	# Generate plain disassembly based on data map
	# TODO:
	# For this to make sense for data objects, we need to put it in a function,
	# then call it *here* for code objects and *later* for data objects (i.e.
	# after analysis of disassembly of code objects, when maps for data objects
	# have been completed)
	#for object in disasm["objects"]:
	#	logging.info("Generating plain disassembly for object %d:" % object["num"])
	#	object["disasm plain"] = []
	#	offset = 0
	#	#length = 0
	#	#disassembly = []
	#	#bad_num = 0
	#	#bad_list = []
	#	for entry in object["data map"]:
	#		if (offset != entry["start"]):
	#			logging.error("Offset != entry[\"start\"]: offset: 0x%x, entry[\"start\"]: 0x%x" % (offset, entry["start"]))
	#			break
	#		if (entry["type"] == "code"):
	#			#(offset, length, disassembly, bad_num, bad_list) = generate_code_disassembly(object["data"], entry["start"], entry["end"], objdump_exec, bad_num)
	#			#(offset, length, disassembly, bad_num, bad_list) = generate_code_disassembly(object["data"], entry["start"], entry["end"], entry["mode"], objdump_exec, bad_num, verbose=False)
	#			(offset, length, disassembly, bads) = generate_code_disassembly(object["data"], entry["start"], entry["end"], entry["mode"], objdump_exec, len(object["disasm plain"]), len(object["bad code"]), verbose=False)
	#			object["bad code"] += bads
	#		elif (entry["type"] == "data"):
	#			(offset, length, disassembly) = generate_data_disassembly(object["data"], entry["start"], entry["end"], entry["mode"])
	#		else:
	#			logging.error("Entry has invalid type: '%s'" % entry["type"])
	#			break
	#		if (offset != entry["end"]):
	#			logging.error("Offset != entry[\"end\"]: offset: 0x%x, entry[\"end\"]: 0x%x" % (offset, entry["end"]))
	#			break
	#		if (length != entry["end"] - entry["start"]):
	#			logging.error("Length != entry[\"end\"] - entry[\"start\"]: length: 0x%x (%d), entry[\"end\"] - entry[\"start\"]: 0x%x (%d)" % (length, length, entry["end"] - entry["start"], entry["end"] - entry["start"]))
	#			break
	#		object["disasm plain"] += disassembly
	#	logging.debug("Size of plain disassembly: %d lines, %d bytes" % (len(disassembly), len(str.join(os.linesep, disassembly))))

	# TODO: improve output on error; currently, it's hard to find out what actually went wrong
	#def generate_plain_disassembly(object):
	#	logging.debug("Generating plain disassembly for object %d..." % object["num"])
	#	object["disasm plain"] = []
	#	offset = 0
	#	#length = 0
	#	#disassembly = []
	#	#bad_num = 0
	#	#bad_list = []
	#	for entry in object["data map"]:
	#		if (offset != entry["start"]):
	#			logging.error("Offset != entry[\"start\"]: offset: 0x%x, entry[\"start\"]: 0x%x" % (offset, entry["start"]))
	#			break
	#		if (entry["type"] == "code"):
	#			#(offset, length, disassembly, bad_num, bad_list) = generate_code_disassembly(object["data"], entry["start"], entry["end"], objdump_exec, bad_num)
	#			#(offset, length, disassembly, bad_num, bad_list) = generate_code_disassembly(object["data"], entry["start"], entry["end"], entry["mode"], objdump_exec, bad_num, verbose=False)
	#			(offset, length, disassembly, bads) = generate_code_disassembly(object["data"], entry["start"], entry["end"], entry["mode"], objdump_exec, len(object["disasm plain"]), len(object["bad code"]), verbose=False)
	#			object["bad code"] += bads
	#		elif (entry["type"] == "data"):
	#			if (entry["mode"].startswith("struct")):
	#				(offset, length, disassembly) = generate_struct_disassembly(object["data"], entry["start"], entry["end"], entry["mode"])
	#			else:
	#				(offset, length, disassembly) = generate_data_disassembly(object["data"], entry["start"], entry["end"], entry["mode"])
	#		else:
	#			logging.error("Entry has invalid type: '%s'" % entry["type"])
	#			break
	#		if (offset != entry["end"]):
	#			logging.error("Offset != entry[\"end\"]: offset: 0x%x, entry[\"end\"]: 0x%x" % (offset, entry["end"]))
	#			break
	#		if (length != entry["end"] - entry["start"]):
	#			logging.error("Length != entry[\"end\"] - entry[\"start\"]: length: 0x%x (%d), entry[\"end\"] - entry[\"start\"]: 0x%x (%d)" % (length, length, entry["end"] - entry["start"], entry["end"] - entry["start"]))
	#			#for line in disassembly:
	#			#	logging.debug(line)
	#			break
	#		object["disasm plain"] += disassembly
	#	logging.debug("Size of plain disassembly: %d lines, %d bytes" % (len(disassembly), len(str.join(os.linesep, disassembly))))

	# NOTE:
	# Same as above, but keeps going on errors (by starting next entry at correct
	# offset, i.e. 'offset = entry["start"]'). Much better this way as the complete
	# disassembly will still be generated and can then be studied for issues
	# TODO:
	# Improve error output; currently, it's hard to figure out what exactly went wrong
	def generate_plain_disassembly(object):
		logging.debug("Generating plain disassembly for object %d..." % object["num"])
		object["disasm plain"] = []
		offset = 0
		#length = 0
		#disassembly = []
		#bad_num = 0
		#bad_list = []
		for entry in object["data map"]:
			if (offset != entry["start"]):
				logging.warning("Offset != entry[\"start\"]: offset: 0x%x, entry[\"start\"]: 0x%x" % (offset, entry["start"]))
				offset = entry["start"]
			if (entry["type"] == "code"):
				#(offset, length, disassembly, bad_num, bad_list) = generate_code_disassembly(object["data"], entry["start"], entry["end"], objdump_exec, bad_num)
				#(offset, length, disassembly, bad_num, bad_list) = generate_code_disassembly(object["data"], entry["start"], entry["end"], entry["mode"], objdump_exec, bad_num, verbose=False)
				(offset, length, disassembly, bads) = generate_code_disassembly(object["data"], entry["start"], entry["end"], entry["mode"], objdump_exec, len(object["disasm plain"]), len(object["bad code"]), verbose=False)
				object["bad code"] += bads
			elif (entry["type"] == "data"):
				if (entry["mode"].startswith("struct")):
					(offset, length, disassembly) = generate_struct_disassembly(object["data"], entry["start"], entry["end"], entry["mode"])
				else:
					(offset, length, disassembly) = generate_data_disassembly(object["data"], entry["start"], entry["end"], entry["mode"])
			else:
				logging.error("Entry has invalid type: '%s'" % entry["type"])
				continue
			if (offset != entry["end"]):
				logging.warning("Offset != entry[\"end\"]: offset: 0x%x, entry[\"end\"]: 0x%x" % (offset, entry["end"]))
			if (length != entry["end"] - entry["start"]):
				logging.warning("Length != entry[\"end\"] - entry[\"start\"]: length: 0x%x (%d), entry[\"end\"] - entry[\"start\"]: 0x%x (%d)" % (length, length, entry["end"] - entry["start"], entry["end"] - entry["start"]))
			object["disasm plain"] += disassembly
		logging.debug("Size of plain disassembly: %d lines, %d bytes" % (len(object["disasm plain"]), len(str.join(os.linesep, object["disasm plain"]))))

	# Generate plain disassembly for code objects
	logging.info("")
	logging.info("Generating plain disassembly for code objects:")
	for object in [ item for item in disasm["objects"] if (item["type"] == "code") ]:
		generate_plain_disassembly(object)


	logging.info("")
	logging.info("Analyzing plain disassembly of code objects:")

	#
	# TODO:
	# This would be a good place to create disassembly line offsets to fixups maps
	# for code objects; we need these for multiple tasks down the road
	#

	# Process disassembly of code objects, analyze branches and add corresponding
	# globals
	# TODO:
	# Need to process fixups here to fix 'faulty' calls/jumps in MK2.EXE. Those
	# calls/jumps point to code in data object (i.e. object 2), e.g. DO_BABALITY
	# @0x2dbe0, ME_IN_FRONT @0x1d97d, ME_IN_BACK, DAMAGE_TO_ME, ...
	# -> identify those calls/jumps; this requires fixup to line offset map
	#    (see fixup_map in generate_formatted_disassembly)
	# -> replace target address with target address of fixup using format '@obj2:
	#    0x...'; this might need to be solved some other way (or someplace else),
	#    as discovered code blocks in data objects will only be disassembled
	#    temporarily here
	# -> if existing, modify global matching fixup target address to be of type
	#    'code'; if missing, add global of type 'code' for target address
	# -> discovered code needs to be analyzed, too (branches, access sizes); this
	#    can lead to further code blocks... -> needs to be done recursive
	# -> this will require putting the whole 'Analyzing plain disassembly' block
	#    into a function so it can be called for newly discovered code blocks
	logging.debug("Analyzing branches...")
	added_globals = 0
	known_globals = { (item["object"], item["offset"]): item for item in disasm["globals"] }
	for object in [ item for item in disasm["objects"] if (item["type"] == "code") ]:
		for i in range(0, len(object["disasm plain"])):
			line = object["disasm plain"][i]
			asm = split_asm_line(line)
			if (asm == None):
				logging.warning("Invalid assembly line: line %d: '%s'" % (i+1, line))
				continue
			if (asm["command"] != "call" and not asm["command"].startswith("j")):	# only call + jump commands
				continue
			match = re.match("^0x([0-9a-fA-F]+)$", asm["arguments"].strip())		# only those with direct/constant address/offset
			if (match == None):
				#logging.warning("Failed to match offset: line %d: %s" % (i+1, line))
				continue
			offset = int(match.group(1), 16)
			if ((object["num"], offset) in known_globals):
				continue
			disasm["globals"].append(OrderedDict([("name", None), ("module", None), ("object", object["num"]), ("offset", offset), ("type", object["type"]), ("source", "branch analysis")]))
			known_globals[(object["num"], offset)] = disasm["globals"][-1]
			added_globals += 1
	disasm["globals"].sort(key=lambda item: (item["object"], item["offset"]))
	logging.debug("Added %d globals for branches" % added_globals)


	# Process disassembly of code objects, analyze lines with fixup/relocation
	# entries, determine access size, add size information to globals
	# TODO:
	# Check if the way this operates makes sense; would this profit from a fixup
	# to disassembly line map?
	logging.debug("Analyzing access sizes...")
	added_as = 0
	globals_map = { (item["object"], item["offset"]): item for item in disasm["globals"] }
	for object in [ item for item in disasm["objects"] if (item["type"] == "code") ]:
		fixup_index = 0
		object_fixups = [ fixup for fixup in disasm["fixups"] if (fixup["source object"] == object["num"]) ]
		object_fixups.sort(key=lambda item: item["source offset"])
		for i in range(0, len(object["disasm plain"])):
			line = object["disasm plain"][i]
			asm = split_asm_line(line)
			if (asm == None):
				logging.warning("Invalid assembly line: line %d: '%s'" % (i+1, line))
				continue
			asm_start = asm["offset"]
			asm_end = asm["offset"] + len(asm["data"])
			asm_fixups = []
			while (fixup_index < len(object_fixups) and object_fixups[fixup_index]["source offset"] >= asm_start and object_fixups[fixup_index]["source offset"] < asm_end):
				asm_fixups.append(object_fixups[fixup_index])
				fixup_index += 1
			if (len(asm_fixups) == 0):
				continue

			for fixup in asm_fixups:
				access_size = None

				# TODO:
				# Investigate further potential candidates:
				# 35cf3:   3e be e2 57 04 00       ds mov esi,0x457e2

				# Check if target offset appears multiple times within disassembly line;
				# If it does, we have to bail out as there is no way to distinguish the
				# target offset from some other static number with the same value
				if (len(re.findall("0x0*%x" % fixup["target offset"], asm["arguments"])) > 1):
					logging.warning("Multiple matches for fixup target offset 0x%x: %s" % (fixup["target offset"], line))
					continue

				# This explicitely tells us the access size of the reference
				#match = re.search("([A-Z]+) PTR (?:[a-z]+:)?0x%x" % fixup["target offset"], asm["arguments"])
				match = re.search("([A-Z]+) PTR (?:cs:|ds:|es:|fs:|gs:|ss:)?0x%x" % fixup["target offset"], asm["arguments"])
				if (match):
					access_size = match.group(1)
					#logging.debug("Explicit (direct address): 0x%x == %s: %s" % (fixup["target offset"], access_size, line))

				# This explicitely tells us that the reference offset by a value (register
				# in most cases) is accessed with a certain size -> with high probability,
				# this tells us that the reference holds a *table* of access_size items
				if (access_size == None):
					#match = re.search("([A-Z]+) PTR (?:[a-z]+:)?\[.+0x%x\]" % fixup["target offset"], asm["arguments"])
					match = re.search("([A-Z]+) PTR (?:cs:|ds:|es:|fs:|gs:|ss:)?\[.+0x%x\]" % fixup["target offset"], asm["arguments"])
					if (match):
						#access_size = match.group(1)
						access_size = match.group(1) + "S"
						#logging.debug("Explicit (indirect address): 0x%x == %s: %s" % (fixup["target offset"], access_size, line))

				# This implicitely tells us the access size of the reference, since mov/cmp
				# use same access size for source and destination
				# NOTE:
				# !! WRONG !!, e.g. 'mov DWORD PTR ds:0x24d1c,0x24e68' -> '0x24e68' is
				# just a value, it doesn't tell us anything about the data size of data
				# at offset '0x24e68'
				#if (access_size == None and (asm["command"] == "mov" or asm["command"] == "cmp")):
				#	match = re.search("([A-Z]+) PTR", asm["arguments"])
				#	if (match):
				#		access_size = match.group(1)
				#		logging.debug("Implicit (mov/cmp src/dst PTR): 0x%x == %s: %s" % (fixup["target offset"], access_size, line))

				# PUSH instruction
				# Access size can be derived from opcode (see https://css.csail.mit.edu/
				# 6.858/2014/readings/i386/PUSH.htm)
				# NOTE: !! WRONG !!, just tells us if a byte/word/dword is being pushed,
				#       but that just refers to the VALUE itself; tells us nothing about
				#       the reference as no dereferencing takes place
				#if (access_size == None and asm["command"] == "push"):
				#	...

				# This implicitely tells us the access size of the reference, based on the
				# source/destination register being used for mov/cmp
				# NOTE:
				# Prefixed '<reg>:' before offset has to be mandatory here, e.g. 'mov ax,
				# ds:0x4ade' tells us something because 'ds:...' is being dereferenced,
				# whereas 'mov ax,0x4ade' only tells us that the VALUE '0x4ade' is a word,
				# but that does not say anything about the reference as no dereferencing
				# takes place

				# NOTE: prefixed '<reg>:' before offset is MANDATORY here
				if (access_size == None and (asm["command"] == "mov" or asm["command"] == "cmp")):
					if (re.search("(eax|ebx|ecx|edx|esp|ebp|esi|edi),(cs:|ds:|es:|fs:|gs:|ss:)0x%x" % fixup["target offset"], asm["arguments"])):
						access_size = "DWORD"
					elif (re.search("(cs:|ds:|es:|fs:|gs:|ss:)0x%x,(eax|ebx|ecx|edx|esp|ebp|esi|edi)" % fixup["target offset"], asm["arguments"])):
						access_size = "DWORD"
					elif (re.search("(ax|bx|cx|dx|sp|bp|si|di),(cs:|ds:|es:|fs:|gs:|ss:)0x%x" % fixup["target offset"], asm["arguments"])):
						access_size = "WORD"
					elif (re.search("(cs:|ds:|es:|fs:|gs:|ss:)0x%x,(ax|bx|cx|dx|sp|bp|si|di)" % fixup["target offset"], asm["arguments"])):
						access_size = "WORD"
					elif (re.search("(al|ah|bl|bh|cl|ch|dl|dh),(cs:|ds:|es:|fs:|gs:|ss:)0x%x" % fixup["target offset"], asm["arguments"])):
						access_size = "BYTE"
					elif (re.search("(cs:|ds:|es:|fs:|gs:|ss:)0x%x,(al|ah|bl|bh|cl|ch|dl|dh)" % fixup["target offset"], asm["arguments"])):
						access_size = "BYTE"
					#if (access_size != None):
					#	logging.debug("Implicit (mov/cmp src/dst reg): 0x%x == %s: %s" % (fixup["target offset"], access_size, line))

				# NOTE: prefixed '<reg>:' before offset is OPTIONAL here
				#if (access_size == None and (asm["command"] == "mov" or asm["command"] == "cmp")):
				#	if (re.search("(eax|ebx|ecx|edx|esp|ebp|esi|edi),(cs:|ds:|es:|fs:|gs:|ss:)?0x%x" % fixup["target offset"], asm["arguments"])):
				#		access_size = "DWORD"
				#	elif (re.search("(cs:|ds:|es:|fs:|gs:|ss:)?0x%x,(eax|ebx|ecx|edx|esp|ebp|esi|edi)" % fixup["target offset"], asm["arguments"])):
				#		access_size = "DWORD"
				#	elif (re.search("(ax|bx|cx|dx|sp|bp|si|di),(cs:|ds:|es:|fs:|gs:|ss:)?0x%x" % fixup["target offset"], asm["arguments"])):
				#		access_size = "WORD"
				#	elif (re.search("(cs:|ds:|es:|fs:|gs:|ss:)?0x%x,(ax|bx|cx|dx|sp|bp|si|di)" % fixup["target offset"], asm["arguments"])):
				#		access_size = "WORD"
				#	elif (re.search("(al|ah|bl|bh|cl|ch|dl|dh),(cs:|ds:|es:|fs:|gs:|ss:)?0x%x" % fixup["target offset"], asm["arguments"])):
				#		access_size = "BYTE"
				#	elif (re.search("(cs:|ds:|es:|fs:|gs:|ss:)?0x%x,(al|ah|bl|bh|cl|ch|dl|dh)" % fixup["target offset"], asm["arguments"])):
				#		access_size = "BYTE"
				#	#if (access_size != None):
				#	#	logging.debug("Implicit (mov/cmp src/dst reg): 0x%x == %s: %s" % (fixup["target offset"], access_size, line))

				# We were unable to determine an access size
				if (access_size == None):
					#logging.warning("Failed to determine access size for offset 0x%x: %s" % (fixup["target offset"], line))
					continue

				# Add access size to global associated with fixup
				# NOTE: this requires that corresponding globals have already been added for fixup references
				key = (fixup["target object"], fixup["target offset"])
				if (not key in globals_map):
					logging.error("No corresponding global found for fixup: source object: %d, source offset: 0x%x, target object: %d, target offset: 0x%x" % (fixup["source object"], fixup["source offset"], fixup["target object"], fixup["target offset"]))
					continue
				if (not "access sizes" in globals_map[key]):
					globals_map[key]["access sizes"] = []
				if (access_size in globals_map[key]["access sizes"]):
					continue
				globals_map[key]["access sizes"].append(access_size)
				added_as += 1

	logging.debug("Added %d access sizes for globals" % added_as)


	# Generate disassembly structure
	#
	# TODO:
	# - modify structure items to all have 'start', 'end', 'length'; when adding 'start' has to be specified, while 'end' and 'length' may be None
	# - modify structure items to have a 'level' (as in tier):
	#   object   -> level 1
	#   module   -> level 2
	#   function -> level 3
	#   branch   -> level 4
	#   variable -> level 3 (if source == 'debug info')
	#   variable -> level 4 (if source == 'fixup data')
	#   virtual padding -> level 100
	#   bad code        -> level 101
	#   hint            -> level 102
	#   -> use levels to determine 'end' and 'length' properties: an item only ends previous items if item["level"] <= previous_item["level"];
	#      levels >= 100 are special: only end previous items of equal level (one could say these items are level-less); use list to keep track
	#      of visited items: append newly visited item, check levels of items before newly appended item
	#   -> don't change 'end'/'length' if already set to != None (e.g. object/bad code/hint/virtual padding length is known right when added)
	#   -> level can also be used to improve/simplify insert_structure_item(): item to insert is inserted a) based on 'start', b) based on level
	#      (insert item after items with lower/equal levels)
	#
	logging.info("")
	logging.info("Generating disassembly structures for all objects:")
	parent_nums = {} # putting this here guarantees consecutive naming across objects, which is very important for merging code + data later
	for object in disasm["objects"]:
		logging.info("Generating disassembly structure for object %d:" % object["num"])
		object["disasm structure"] = []

		logging.debug("Adding object start...")
		insert_structure_item(object["disasm structure"], OrderedDict([("type", "object start"), ("start", 0), ("end", object["size"]), ("length", object["size"]), ("name", "Object %d" % object["num"]), ("label", "object_%d" % object["num"]), ("objnum", object["num"])]))

		if (object["actual data size"] < object["virtual memory size"]):
			logging.debug("Adding virtual size padding start...")
			#insert_structure_item(object["disasm structure"], OrderedDict([("type", "virtual padding start"), ("offset", object["actual data size"]), ("name", "Virtual padding"), ("label", "virtual_padding"), ("size", object["virtual memory size"] - object["actual data size"]), ("objnum", object["num"])]))
			#insert_structure_item(object["disasm structure"], OrderedDict([("type", "virtual padding start"), ("start", object["actual data size"] + 1), ("end", object["size"]), ("length", object["size"] - object["actual data size"] - 1), ("name", "Virtual padding"), ("label", "virtual_padding"), ("size", object["virtual memory size"] - object["actual data size"]), ("objnum", object["num"])]))
			insert_structure_item(object["disasm structure"], OrderedDict([("type", "virtual padding start"), ("start", object["actual data size"]), ("end", object["size"]), ("length", object["size"] - object["actual data size"]), ("name", "Virtual padding"), ("label", "virtual_padding"), ("size", object["virtual memory size"] - object["actual data size"]), ("objnum", object["num"])]))

		#logging.debug("Adding modules...")
		#added_items = 0
		#for module in disasm["modules"]:
		#	for offset in module["offsets"]:
		#		if (offset["object"] != object["num"]):
		#			continue
		#		insert_structure_item(object["disasm structure"], OrderedDict([("type", "module"), ("start", offset["offset"]), ("end", offset["offset"] + offset["size"]), ("length", offset["size"]), ("name", module["name"]), ("label", ntpath.basename(module["name"]).replace(".", "_").lower()), ("modnum", module["num"])]))
		#		added_items += 1
		#logging.debug("Added %d modules" % added_items)
		# NOTE: split into module start + end (based on hints below)
		logging.debug("Adding modules...")
		added_items = 0
		for module in disasm["modules"]:
			for offset in module["offsets"]:
				if (offset["object"] != object["num"]):
					continue
				start_item = insert_structure_item(object["disasm structure"], OrderedDict([("type", "module start"), ("start", offset["offset"]), ("end", offset["offset"] + offset["size"]), ("length", offset["size"]), ("name", module["name"]), ("label", ntpath.basename(module["name"]).replace(".", "_").lower()), ("modnum", module["num"])]))
				insert_structure_item(object["disasm structure"], OrderedDict([("type", "module end"), ("start", offset["offset"] + offset["size"]), ("end", offset["offset"] + offset["size"]), ("length", 0), ("name", module["name"]), ("label", ntpath.basename(module["name"]).replace(".", "_").lower()), ("modnum", module["num"])]), ins_mode="end", start_item=start_item)
				added_items += 1
		logging.debug("Added %d modules" % added_items)

		# TODO:
		# Although this is already a good spot for this, the *perfect* spot would
		# probably be after functions, but before branches, variables and references
		# TODO:
		# The end item with length == 0 is somewhat cumbersome, but works ok for now
		logging.debug("Adding hints...")
		added_items = 0
		for hint in object["hints"]:
			start_item = insert_structure_item(object["disasm structure"], OrderedDict([("type", "hint start"), ("start", hint["start"]), ("end", hint["end"]), ("length", hint["length"]), ("name", "Hint %d" % hint["num"]), ("label", "hint_%d" % hint["num"]), ("hintnum", hint["num"]), ("hinttype", hint["type"]), ("hintmode", hint["mode"]), ("hintlength", hint["length"])] + ([("hintcomment", hint["comment"])] if ("comment" in hint) else [])), ins_mode="start")
			insert_structure_item(object["disasm structure"], OrderedDict([("type", "hint end"), ("start", hint["end"]), ("end", hint["end"]), ("length", 0), ("name", "Hint %d" % hint["num"]), ("label", "hint_%d" % hint["num"]), ("hintnum", hint["num"])]), ins_mode="end", start_item=start_item)
			added_items += 1
		logging.debug("Added %d hints" % added_items)

		# TODO:
		# Modify insert_structure_item() to allow 'None' for name + label
		# -or-
		# check if we can name unnamed globals / structure items right here
		# - could modify insert_structure_item() to return index of inserted item + create get_structure_item_parent() to determine parent
		# - could modify insert_structure_item() to search and return parent
		# - could modify insert_structure_item() to determine parent and add name + label if None
		# - could create get_structure_parent(offset) to search for appropriate parent
		#   -> probably best solution, allows us to name global first, then insert structure item with name + label already in place
		#   -> no change to insert_structure_item() required, no link between globals and structure items required
		# (for now, using str() to convert None to 'None')
		# TODO:
		# Branches can have 'sizes' attribute if data occurrs in code (e.g. MK1.EXE, 'dllload_c_branch_1');
		# but currently, sizes are only added as comments for variables in generate_formatted_disassembly()
		logging.debug("Adding globals...")
		added_functions = 0
		added_branches = 0
		added_variables = 0
		added_total = 0
		#incomplete_map = {}
		sitem_global_map = {}
		for global_ in disasm["globals"]:
			if (global_["object"] != object["num"]):
				continue
			if (global_["type"] == "code"):
				if (global_["source"] == "debug info"):
					sitem = insert_structure_item(object["disasm structure"], OrderedDict([("type", "function"), ("start", global_["offset"]), ("end", None), ("length", None), ("name", global_["name"]), ("label", global_["name"]), ("source", global_["source"])]))
					added_functions += 1
				elif (global_["source"] == "fixup data"):
					#sitem = insert_structure_item(object["disasm structure"], OrderedDict([("type", "reference"), ("start", global_["offset"]), ("name", global_["name"]), ("label", global_["name"])]))
					#sitem = insert_structure_item(object["disasm structure"], OrderedDict([("type", "branch"), ("start", global_["offset"]), ("end", None), ("length", None), ("name", global_["name"]), ("label", global_["name"]), ("source", global_["source"])]))
					sitem = insert_structure_item(object["disasm structure"], OrderedDict([("type", "reference"), ("start", global_["offset"]), ("end", None), ("length", None), ("name", global_["name"]), ("label", global_["name"]), ("source", global_["source"])]))
					added_branches += 1
				elif (global_["source"] == "branch analysis"):
					sitem = insert_structure_item(object["disasm structure"], OrderedDict([("type", "branch"), ("start", global_["offset"]), ("end", None), ("length", None), ("name", global_["name"]), ("label", global_["name"]), ("source", global_["source"])]))
					added_branches += 1
				else:
					logging.error("Invalid global source: '%s'" % global_["source"])
					continue
			elif (global_["type"] == "data"):
				sitem = insert_structure_item(object["disasm structure"], OrderedDict([("type", "variable"), ("start", global_["offset"]), ("end", None), ("length", None), ("name", global_["name"]), ("label", global_["name"]), ("source", global_["source"])]))
				added_variables += 1
			added_total += 1
			if ("access sizes" in global_):
				sitem["access sizes"] = global_["access sizes"]
			##if (sitem["name"] == None or sitem["label"] == None):
			##if (not (all(sitem[key] != None for key in sitem) and all(global_[key] != None for key in global_))): # if some value in sitem or global is None, sitem + global are considered incomplete
			##if (any(sitem[key] == None for key in sitem) or any(global_[key] == None for key in global_))): # if some value in sitem or global is None, sitem + global are considered incomplete
			#if (any(value == None for key, value in sitem.items()) or any(value == None for key, value in global_.items())): # if some value in sitem or global is None, sitem + global are considered incomplete
			#	#assert not sitem in incomplete_map # NOTE: will not work as dicts are not hashable -> use id()
			#	#incomplete_map[sitem] = global_
			#	assert not id(sitem) in incomplete_map
			#	incomplete_map[id(sitem)] = global_
			assert not id(sitem) in sitem_global_map
			sitem_global_map[id(sitem)] = global_
		#logging.debug("Added %d globals (%d functions, %d branches, %d variables), %d incomplete" % (added_total, added_functions, added_branches, added_variables, len(incomplete_map)))
		logging.debug("Added %d globals (%d functions, %d branches, %d variables)" % (added_total, added_functions, added_branches, added_variables))

		if (object["type"] == "code"):
			logging.debug("Adding bad code sections...")
			added_items = 0
			for bad in object["bad code"]:
				start_item = insert_structure_item(object["disasm structure"], OrderedDict([("type", "bad code start"), ("start", bad["start"]), ("end", bad["end"]), ("length", bad["length"]), ("name", "Bad code %d" % bad["num"]), ("label", "bad_code_%d" % bad["num"]), ("badnum", bad["num"]), ("badtype", bad["type"]), ("badcontext", bad["context"]), ("badlength", bad["length"])]), ins_mode="start")
				insert_structure_item(object["disasm structure"], OrderedDict([("type", "bad code end"), ("start", bad["end"]), ("end", bad["end"]), ("length", 0), ("name", "Bad code %d" % bad["num"]), ("label", "bad_code_%d" % bad["num"]), ("badnum", bad["num"])]), ins_mode="end", start_item=start_item)
				added_items += 1
			logging.debug("Added %d bad code sections" % added_items)

		if (object["actual data size"] < object["virtual memory size"]):
			logging.debug("Adding virtual size padding end...")
			insert_structure_item(object["disasm structure"], OrderedDict([("type", "virtual padding end"), ("start", object["size"]), ("end", object["size"]), ("length", 0), ("name", "Virtual padding"), ("label", "virtual_padding")]))

		logging.debug("Adding object end...")
		insert_structure_item(object["disasm structure"], OrderedDict([("type", "object end"), ("start", object["size"]), ("end", object["size"]), ("length", 0), ("name", "Object %d" % object["num"]), ("label", "object_%d" % object["num"]), ("objnum", object["num"])]))

		# TESTING: Process structure, complete incomplete structure items and associated globals
		# NOTE: relies on incomplete_map created above
		# NOTE: relies on parent_nums declared outside of loop
		#logging.debug("Completing incomplete structure items / globals...")
		#parent = None
		##parent_nums = {} # declared outside of loop, see above
		#module = None
		#completed = 0
		#for sitem in object["disasm structure"]:
		#	#if (sitem in incomplete_map):
		#	#	global_ = incomplete_map[sitem]
		#	if (id(sitem) in incomplete_map):
		#		global_ = incomplete_map[id(sitem)]
		#		if (parent != None):
		#			#if (not sitem["type"] in parent_nums[id(parent)]):
		#			#	parent_nums[id(parent)][sitem["type"]] = 0
		#			#parent_nums[id(parent)][sitem["type"]] += 1
		#			#sitem["name"] = "%s %s %d" % (parent["name"], sitem["type"], parent_nums[id(parent)][sitem["type"]])
		#			#sitem["label"] = "%s_%s_%d" % (parent["label"], sitem["type"], parent_nums[id(parent)][sitem["type"]])
		#			if (not sitem["type"] in parent_nums[parent["name"]]): # NOTE: using parent["name"] as key guarantees consecutive naming even if items show up more than once (e.g. MK1.EXE, object 2, module 0 'kombat.cpp')
		#				parent_nums[parent["name"]][sitem["type"]] = 0
		#			parent_nums[parent["name"]][sitem["type"]] += 1
		#			sitem["name"] = "%s %s %d" % (parent["name"], sitem["type"], parent_nums[parent["name"]][sitem["type"]])
		#			sitem["label"] = "%s_%s_%d" % (parent["label"], sitem["type"], parent_nums[parent["name"]][sitem["type"]])
		#			global_["name"] = sitem["label"]
		#			global_["module"] = module
		#			completed += 1
		#		else:
		#			logging.error("No parent to complete incomplete structure item / global (item: %s, global: %s)" % (str(sitem), str(global_)))
		#	if (sitem["type"] in ("object start", "module", "function")):
		#		parent = sitem
		#		if (not parent["name"] in parent_nums):
		#			#parent_nums[id(parent)] = {}
		#			parent_nums[parent["name"]] = {}
		#		if (sitem["type"] == "module"):
		#			module = sitem["modnum"]
		#logging.debug("Completed incomplete %d structure items / globals" % completed)

		# Process and finalize structure:
		# - name unnamed items and update associated globals
		# - size unsized items and update associated globals
		# NOTE: relies on sitem_global_map created above
		# NOTE: relies on parent_nums declared outside of loop
		logging.debug("Finalizing structure...")
		parent = None
		#parent_nums = {} # declared outside of loop, see above
		module = None
		named_sitems = 0
		named_globals = 0
		sitems_to_size = []
		sized_sitems = 0
		sized_globals = 0
		for sitem in object["disasm structure"]:

			# [Naming] Keep track of current parent and numbering
			#if (sitem["type"] in ("object start", "module", "function")):
			#if (sitem["type"] in ("object start", "module", "function") or (sitem["type"] == "variable" and sitem["source"] == "debug info")):
			if (sitem["type"] in ("object start", "module start", "function") or (sitem["type"] == "variable" and sitem["source"] == "debug info")):
				parent = sitem
				if (not parent["name"] in parent_nums):
					parent_nums[parent["name"]] = {}
				if (sitem["type"] == "module start"):
					module = sitem["modnum"]

			# [Naming] Name unnamed items based on current parent, update associated globals
			if (sitem["name"] == None or sitem["label"] == None):
				assert parent != None
				if (not sitem["type"] in parent_nums[parent["name"]]):
					parent_nums[parent["name"]][sitem["type"]] = 0
				parent_nums[parent["name"]][sitem["type"]] += 1
				sitem["name"] = "%s %s %d" % (parent["name"], sitem["type"], parent_nums[parent["name"]][sitem["type"]])
				sitem["label"] = "%s_%s_%d" % (parent["label"], sitem["type"], parent_nums[parent["name"]][sitem["type"]])
				named_sitems += 1
				if (id(sitem) in sitem_global_map):
					global_ = sitem_global_map[id(sitem)]
					global_["name"] = sitem["label"]
					global_["module"] = module
					named_globals += 1

			# [Sizing] These kinds of items terminate all currently tracked items. Set ends
			#          and determine sizes, update associated globals, reset tracking list
			#if (sitem["type"] in ("object start", "object end", "module", "function") or (sitem["type"] == "variable" and sitem["source"] == "debug info")):
			if (sitem["type"] in ("object start", "object end", "module start", "module end", "function") or (sitem["type"] == "variable" and sitem["source"] == "debug info")):
				for sitem2 in sitems_to_size:
					sitem2["end"] = sitem["start"]
					sitem2["length"] = sitem2["end"] - sitem2["start"]
					sized_sitems += 1
					if (id(sitem2) in sitem_global_map):
						global_ = sitem_global_map[id(sitem2)]
						global_["length"] = sitem2["length"]
						sized_globals += 1
				if (sitem["type"] == "module end"):
					module = None
				sitems_to_size = []

			# [Sizing] These kinds of items terminate the last currently tracked item if
			#          its the same kind. Untrack item, set end, determine size, update
			#          associated global
			elif (sitem["type"] in ("branch", "variable") and len(sitems_to_size) > 0 and sitems_to_size[-1]["type"] in ("branch", "variable") and sitems_to_size[-1]["source"] != "debug info"):
				sitem2 = sitems_to_size.pop()
				sitem2["end"] = sitem["start"]
				sitem2["length"] = sitem2["end"] - sitem2["start"]
				sized_sitems += 1
				if (id(sitem2) in sitem_global_map):
					global_ = sitem_global_map[id(sitem2)]
					global_["length"] = sitem2["length"]
					sized_globals += 1

			# [Sizing] Track items that need to be sized
			if (sitem["type"] in ("function", "branch", "variable")):
				sitems_to_size.append(sitem)

		logging.debug("Named %d structure items and %d globals" % (named_sitems, named_globals))
		logging.debug("Sized %d structure items and %d globals" % (sized_sitems, sized_globals))

		# Structure complete, print stats
		print_structure_stats(object["disasm structure"])


	# TODO:
	# Extend data maps of data objects by making use of size information stored in globals
	# -or-
	# Move entire map creation process for data objects here as this is the point where we
	# have all relevant information at hand; if deciding to move, also move extending based
	# on fixups here from above
	# TODO:
	# Structs like 'MK1.EXE, mksel_asm_variable_3' (WORDs mixed with DWORDs) are going to be
	# tough...
	logging.info("")
	logging.info("Building data maps for data objects:")

	# Step 1: modules + hints (code copied from code objects above)
	#logging.debug("Building initial data maps from modules and hints...")
	# Step 1: object and modules
	logging.debug("Building initial data maps from object and modules...")
	for object in [ item for item in disasm["objects"] if (item["type"] == "data") ]:

		# Initialize data map with object item spanning accross all data
		object["data map"] = [ OrderedDict([("start", 0), ("end", object["size"]), ("type", object["type"]), ("mode", "default"), ("source", "object")]) ]

		# Modules
		for module in disasm["modules"]:
			for offset in [ item for item in module["offsets"] if (item["object"] == object["num"]) ]:
				try:
					insert_data_map_item(object["data map"], OrderedDict([("start", offset["offset"]), ("end", offset["offset"] + offset["size"]), ("type", object["type"]), ("mode", "default"), ("source", "module")]))
				except DataMapInsertError as dmie:
					logging.warning("%s: module: num: %d, start: 0x%x, end: 0x%x, length: 0x%x (%d), name: %s" % (str(dmie), module["num"], offset["offset"], offset["offset"] + offset["size"], offset["size"], offset["size"], module["name"]))

		# Hints
		# NOTE:
		# Hints are inserted as immutable items since we want hints to have precedence
		# over other items (e.g. MK1.EXE, object 2, offset 0xd902)
		# NOTE:
		# Moved to 'Step 4' due to new data map insertion method that does not utilize
		# immutable items
		#for hint in object["hints"]:
		#	try:
		#		insert_data_map_item(object["data map"], OrderedDict([("start", hint["start"]), ("end", hint["end"]), ("type", hint["type"]), ("mode", hint["mode"]), ("source", "hint")]))
		#	except DataMapInsertError as dmie:
		#		#logging.warning("%s: hint %d: start: 0x%x, end: 0x%x, length: 0x%x (%d), type: %s, mode: %s" % (str(dmie), hint["num"], hint["start"], hint["end"], hint["length"], hint["length"], hint["type"], hint["mode"]))
		#		logging.warning("%s: hint: num: %d, start: 0x%x, end: 0x%x, length: 0x%x (%d), type: %s, mode: %s" % (str(dmie), hint["num"], hint["start"], hint["end"], hint["length"], hint["length"], hint["type"], hint["mode"]))

		logging.debug("Data map for object %d has %d entries" % (object["num"], len(object["data map"])))


	# Step 2: size information stored in structure
	logging.debug("Extending data maps based on size information in structure...")
	for object in [ item for item in disasm["objects"] if (item["type"] == "data") ]:
		for sitem in object["disasm structure"]:

			if (not sitem["type"] in ("function", "branch", "variable")):
				continue

			if (sitem["type"] in ("function", "branch")):
				type_ = "code"
				mode = "default"

			elif (sitem["type"] == "variable"):
				type_ = "data"
				#mode = "default"
				if ("access sizes" in sitem):
					if ("BYTE" in sitem["access sizes"] or "BYTES" in sitem["access sizes"]):
						mode = "bytes"
					elif ("WORD" in sitem["access sizes"] or "WORDS" in sitem["access sizes"]):
						mode = "words"
					elif ("DWORD" in sitem["access sizes"] or "DWORDS" in sitem["access sizes"]):
						mode = "dwords"
					elif ("FWORD" in sitem["access sizes"] or "FWORDS" in sitem["access sizes"]):
						mode = "fwords"
					elif ("QWORD" in sitem["access sizes"] or "QWORDS" in sitem["access sizes"]):
						mode = "qwords"
					else:
						logging.error("Failed to interpret access size: %s" % (str(sitem["access sizes"])))
						mode = "default"
				else:
					#mode = "default"
					mode = "auto-strings"

			try:
				insert_data_map_item(object["data map"], OrderedDict([("start", sitem["start"]), ("end", sitem["end"]), ("type", type_), ("mode", mode), ("source", "structure")]))
			except DataMapInsertError as dmie:
				logging.warning("%s: sitem: type: %s, start: 0x%x, end: 0x%x, length: 0x%x (%d), name: %s, label: %s" % (str(dmie), sitem["type"], sitem["start"], sitem["end"], sitem["length"], sitem["length"], sitem["name"], sitem["label"]))

	logging.debug("Data map for object %d has %d entries" % (object["num"], len(object["data map"])))


	# Step 3: fixup references
	logging.debug("Extending data maps based on fixups...")
	for object in [ item for item in disasm["objects"] if (item["type"] == "data") ]:
		for fixup in [ item for item in disasm["fixups"] if (item["source object"] == object["num"]) ]:
			try:
				insert_data_map_item(object["data map"], OrderedDict([("start", fixup["source offset"]), ("end", fixup["source offset"] + 4), ("type", "data"), ("mode", "dwords"), ("source", "fixup")]))
			except DataMapInsertError as dmie:
				#logging.warning("%s: fixup %d: source object: %d, source offset: 0x%x, target object: %d, target offset: 0x%x" % (str(dmie), fixup["num"], fixup["source object"], fixup["source offset"], fixup["target object"], fixup["target offset"]))
				logging.warning("%s: fixup: num: %d, source object: %d, source offset: 0x%x, target object: %d, target offset: 0x%x" % (str(dmie), fixup["num"], fixup["source object"], fixup["source offset"], fixup["target object"], fixup["target offset"]))
	logging.debug("Data map for object %d has %d entries" % (object["num"], len(object["data map"])))


	# Step 4: hints
	# NOTE:
	# Hints need to be added last so they can take precedence over existing items
	# (e.g. MK1.EXE, object 2, offset 0xd902: hint takes precedence over variable
	# 'mkhstd_asm_variable_15')
	logging.debug("Finalizing data maps based on hints...")
	for object in [ item for item in disasm["objects"] if (item["type"] == "data") ]:
		for hint in object["hints"]:
			if (hint["mode"] == "comment"): # skip comment-only hints (no use for data map)
				continue
			try:
				insert_data_map_item(object["data map"], OrderedDict([("start", hint["start"]), ("end", hint["end"]), ("type", hint["type"]), ("mode", hint["mode"]), ("source", "hint")]))
			except DataMapInsertError as dmie:
				#logging.warning("%s: hint %d: start: 0x%x, end: 0x%x, length: 0x%x (%d), type: %s, mode: %s" % (str(dmie), hint["num"], hint["start"], hint["end"], hint["length"], hint["length"], hint["type"], hint["mode"]))
				logging.warning("%s: hint: num: %d, start: 0x%x, end: 0x%x, length: 0x%x (%d), type: %s, mode: %s" % (str(dmie), hint["num"], hint["start"], hint["end"], hint["length"], hint["length"], hint["type"], hint["mode"]))
	logging.debug("Data map for object %d has %d entries" % (object["num"], len(object["data map"])))


	# Step 5: check consistency
	for object in [ item for item in disasm["objects"] if (item["type"] == "data") ]:
		logging.debug("Checking consistency of data map for object %d..." % object["num"])
		check_data_map_consistency(object["num"], object["data map"])


	# Generate plain disassembly for data objects
	logging.info("")
	logging.info("Generating plain disassembly for data objects:")
	for object in [ item for item in disasm["objects"] if (item["type"] == "data") ]:
		generate_plain_disassembly(object)


	#
	# TODO:
	# This would be a good place to create disassembly line offsets to fixups maps
	# for data objects; we need these to help generate the formatted disassembly
	#


	# Generate formatted dissassembly
	# TODO: just a stub for now; generate_formatted_disassembly() needs to be rewritten/revised
	# TODO: generates module maps needed to split formatted disassembly into separate files below for now; should be extracted and done separately
	# TODO: this currently uses fixrel instead of preprocessed fixups; should use fixups if possible
	logging.info("")
	logging.info("Generating formatted disassembly for all objects:")
	for object in disasm["objects"]:
		generate_formatted_disassembly(object, disasm["globals"], fixrel)


	# Write results to files
	logging.info("")
	logging.info("Writing disassembly results to files:")
	files_written = 0
	write_file(outfile_template % "disasm_data_all.txt", format_pprint(disasm))
	#write_file(outfile_template % "disasm_data_objects.txt", format_pprint([OrderedDict([(key, value) for key, value in object_.items() if (not key.startswith("disasm"))]) for object_ in disasm["objects"]]))
	write_file(outfile_template % "disasm_data_objects.txt", format_pprint(disasm["objects"]))
	write_file(outfile_template % "disasm_data_modules.txt", format_pprint(disasm["modules"]))
	write_file(outfile_template % "disasm_data_globals.txt", format_pprint(disasm["globals"]))
	write_file(outfile_template % "disasm_data_fixups.txt", format_pprint(disasm["fixups"]))
	files_written += 5
	for object in disasm["objects"]:
		write_file(outfile_template % "disasm_object_%d_data_binary.bin" % object["num"], object["data"])
		write_file(outfile_template % "disasm_object_%d_disassembly_structure.txt" % object["num"], format_pprint(object["disasm structure"]))
		write_file(outfile_template % "disasm_object_%d_disassembly_plain.asm" % object["num"], object["disasm plain"])
		write_file(outfile_template % "disasm_object_%d_disassembly_formatted.asm" % object["num"], object["disasm formatted"])
		write_file(outfile_template % "disasm_object_%d_disassembly_data_map.txt" % object["num"], format_pprint(object["data map"]))
		files_written += 5
	logging.debug ("Wrote %d files" % files_written)


	# TESTING: Split formatted disassembly into separate files
	# NOTE: relies on module maps being generated by generate_formatted_disassembly()
	logging.info("")
	logging.info("Splitting formatted disassembly into separate files:")
	output_library = []
	modules_separate = 0
	modules_library = 0
	for module in disasm["modules"]:
		output_module = []
		for object in disasm["objects"]:
			if (not module["num"] in object["module map"]):
				continue
			for entry in object["module map"][module["num"]]:
				if (len(output_module) > 0):
					output_module.append("")
				output_module += object["disasm formatted"][entry["start"]:entry["end"]]
		file_name = ntpath.basename(module["name"])
		if (not "." in file_name.lower()): # library modules just have names (i.e. no extension)
			output_library += output_module
			modules_library += 1
			continue
		if (not file_name.lower().endswith(".asm")):
			file_name += ".asm"
		#logging.debug("File '%s'..." % file_name)
		write_file(outfile_template % "modules/%s" % file_name, output_module)
		modules_separate += 1
	write_file(outfile_template % "modules/library.asm", output_library)
	logging.debug("Wrote %d modules to separate files" % modules_separate)
	logging.debug("Wrote %d modules to 'library.asm'" % modules_library)


	# Return results
	return disasm
