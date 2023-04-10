#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#                                                                         -
#  Watcom Disassembly Tool (wcdatool)                                     -
#  Main Part Wdump                                                        -
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 06/03/22                                              -
#                                                                         -
# -------------------------------------------------------------------------


# -------------------------------------
#                                     -
#  TODO                               -
#                                     -
# -------------------------------------

# - nothing atm


# -------------------------------------
#                                     -
#  Exports                            -
#                                     -
# -------------------------------------

__all__ = [ "wdump_parse_output" ]


# -------------------------------------
#                                     -
#  Imports                            -
#                                     -
# -------------------------------------

import logging
import re
import subprocess
from collections import OrderedDict
from modules.module_miscellaneous import *
from modules.module_pretty_print import *


# -------------------------------------
#                                     -
#  Code                               -
#                                     -
# -------------------------------------

# Splits key value pair of wdump output line; wdump format: 'key = value', e.g. 'file offset = 0000F474H'
# NOTE: whitespace in line needs to be reduced to single characters prior to calling this
# NOTE: key regex is non-greedy, e.g. 'offset = 1234H = 5678H' -> ('offset', '1234H = 5678H')
# NOTE: pipe character '|' only ever seems to appear as separator in value string of flag list -> split string into list
def wdump_split_keyval(line):
	match = re.match("^(.+?) = (.+)$", line)
	if (match):
		key = match.group(1).lower()
		value = match.group(2)
		if (re.match("^[0-9a-fA-F]+H$", value)):
			value = int(value[0:-1], 16)
		elif ("|" in value):
			value = [ item.strip().lower() for item in str.split(value, "|") ]
		return key, value
	return None, None

# Decodes wdump section data
def wdump_decode_data(section):

	#                                 DOS EXE Header
	# ==============================================================================
	# length of load module mod 200H                       =     008CH
	# number of 200H pages in load module                  =     0017H
	# ...
	#
	# segment:offset
	#   0000:0020   0000:0028   0000:098C   0000:0994   0000:09A0   0000:09A6
	#   0000:09AA   0000:09AE   0000:09B4   0000:09B6   0000:09F1   01BD:0000
	#   ...
	#
	# load module =
	# 0000:  CC EB FD 90 90 90 90 00  53 52 56 57 B8 22 00 E8            SRVW "
	# 0010:  AA 00 85 C0 74 24 BF EC  03 89 C6 57 AC 88 05 47        t$     W   G
	# 0020:  3C 00 75 F8 5F 89 F8 BA  31 00 E8 EC 00 89 F8 E8    < u _   1
	# ...
	#
	# Additional file data follows DOS executable.
	#
	if (section["name"].startswith("DOS EXE Header")):
		decoded_data = OrderedDict()
		for line in section["data"]:
			line2 = str.join(" ", line.split())
			if (line2 == "segment:offset" or line2 == "load module ="):
				break
			key, value = wdump_split_keyval(line2)
			if (key != None and value != None):
				decoded_data[key] = value
				continue
			logging.warning("invalid data: '%s'" % line2)

	#                            DOS/16M EXE Header - BW
	# ==============================================================================
	# file offset = 0000F474H
	#
	#                               DOS/16M EXE Header
	# ==============================================================================
	# length of load module mod 200H                       =     01E0H
	# number of 200H pages in load module                  =     00B8H
	# ...
	# GLU version                                          = 2. 72
	# original name: 4GWPRO.EXP
	#
	# GDT selectors:
	#                                 Size in    Size in
	# Sel #    Access    File offset   File       Memory     DPL    Present    Flags
	# -----    ------    -----------   -------    -------    ---    -------    -----
	# 0080      ER         00F564       05F90      05F90     0         1
	# 0088      ER         0154F4       0C1C0      0C1C0     0         1
	# ...
	#
	# Relocations selector:offset
	#
	# 0080:054A 0080:057B 0080:05B9 0080:073F
	# 0080:079C 0080:095C 0080:0B76 0080:0BF9
	# ...
	#
	# Load selector = 0080
	#
	# 0000:  E8 6D 05 00 E8 69 05 01  E8 65 05 02 E8 61 05 03     m   i   e   a
	# 0010:  E8 5D 05 04 E8 59 05 05  E8 55 05 06 E8 51 05 07     ]   Y   U   Q
	# ...
	# NOTE: everything after 'GDT selectors:' is ignored
	elif (section["name"].startswith("DOS/16M EXE Header")):
		decoded_data = OrderedDict()
		for line in section["data"]:
			line2 = str.join(" ", line.split())
			if (line2 == "GDT selectors:"):
				break
			if (line2.startswith("original name:")):
				key, value = [ item.strip() for item in line2.split(":", 1) ]
				decoded_data[key] = value
				continue
			key, value = wdump_split_keyval(line2)
			if (key != None and value != None):
				decoded_data[key] = value
				continue
			logging.warning("invalid data: '%s'" % line2)

	#                       Linear EXE Header (OS/2 V2.x) - LE
	# ==============================================================================
	# file offset = 00002C90H
	#
	# byte order (0==little endian, 1==big endian)      =       00H
	# word order       "                "               =       00H
	# ...
	# Module Flags = PROGRAM | WINDOWCOMPAT
	#
	elif (section["name"].startswith("Linear EXE Header (OS/2 V2.x) - LE")):
		decoded_data = OrderedDict()
		for line in section["data"]:
			line2 = str.join(" ", line.split())
			key, value = wdump_split_keyval(line2)
			if (key != None and value != None):
				decoded_data[key] = value
				continue
			logging.warning("invalid data: '%s'" % line2)

	#                                  Object Table
	# ==============================================================================
	# object  1: virtual memory size             = 0003B2D5H
	#           relocation base address          = 00010000H
	#           object flag bits                 = 00002045H
	#           object page table index          = 00000001H
	#           # of object page table entries   = 0000003CH
	#           reserved                         = 00000000H
	#           flags = READABLE|EXECUTABLE|PRELOAD|BIG
	#     page #   1  map page = 000001H file ofs = 0002A400H flgs = 00H Valid
	#
	# segment # 1   offset: 0002A400
	# ===========
	# 0000:  CC EB FD 90 90 90 90 90  90 90 90 90 90 90 90 90
	# 0010:  53 51 52 56 57 55 8B 1D  48 98 04 00 89 C6 83 3D    SQRVWU  H      =
	# ...
	# 0FF0:  04 00 E8 AA BA 02 00 83  C4 0C 89 F8 E8 C2 BA 02
	#
	#
	#     page #   2  map page = 000002H file ofs = 0002B400H flgs = 00H Valid
	#
	# segment # 2   offset: 0002B400
	# ===========
	# 0000:  00 80 BC 24 C4 00 00 00  00 0F 84 51 01 00 00 8B       $       Q
	# 0010:  84 24 C0 00 00 00 BF 01  00 00 00 8B 00 8B 1D A4     $
	# ...
	elif (section["name"].startswith("Object Table")):
		decoded_data = OrderedDict()
		current_object = None
		current_page = None
		current_segment = None
		for line in section["data"]:
			line2 = str.join(" ", line.split())

			# Skip '='-only lines
			if (re.match("^[=]+$", line2)):
				continue

			# New object
			match = re.match("^object ([0-9]+): (.+)$", line2)
			if (match):
				num = int(match.group(1))
				decoded_data[num] = OrderedDict([("num", num)])
				current_object = decoded_data[num]
				line2 = match.group(2)

			# New page
			match = re.match("^page # ([0-9]+) map page = ([0-9a-fA-F]+)H file ofs = ([0-9a-fA-F]+)H flgs = ([0-9a-fA-F]+)H (.+)$", line2)
			if (match):
				if (current_object == None):
					logging.warning("stray page: '%s'" % line2)
					continue
				if (not "pages" in current_object):
					current_object["pages"] = OrderedDict()
				num = int(match.group(1))
				current_object["pages"][num] = OrderedDict([("num", num), ("map page", int(match.group(2), 16)), ("file offset", int(match.group(3), 16)), ("flags", int(match.group(4), 16)), ("valid", True if (match.group(5) == "Valid") else False), ("segments", OrderedDict())])
				current_page = current_object["pages"][num]
				continue

			# New segment
			match = re.match("^segment # ([0-9]+) offset: ([0-9a-fA-F]+)$", line2)
			if (match):
				if (current_page == None):
					logging.warning("stray segment: '%s'" % line2)
					continue
				#current_page["segments"].append( { "num": int(match.group(1)), "offset": int(match.group(2), 16), "data": b'' } )
				#current_segment = current_page["segments"][-1]
				num = int(match.group(1))
				current_page["segments"][num] = OrderedDict([("num", num), ("offset", int(match.group(2), 16)), ("data", b'')])
				current_segment = current_page["segments"][num]
				continue

			# Segment data (NOTE: matching against original line here to correctly capture hex data)
			match = re.match("^([0-9a-fA-F]+):  ([0-9a-fA-F ]+)    (.{16})$", line)
			if (match):
				if (current_segment == None):
					logging.warning("stray segment data: '%s'" % line2)
					continue
				hexdata = str.join(" ", match.group(2).split())
				current_segment["data"] += bytes.fromhex(hexdata)
				continue

			# Object data
			if (current_object == None):
				logging.warning("stray object data: '%s'" % line2)
				continue
			key, value = wdump_split_keyval(line2)
			if (key != None and value != None):
				current_object[key] = value
				continue

			logging.warning("invalid data: '%s'" % line2)

	#                              Resident Names Table
	# ==============================================================================
	# ordinal 0000: mk1
	#
	elif (section["name"].startswith("Resident Names Table")):
		decoded_data = str.join("", section["data"])

	#                                Fixup Page Table
	# ==============================================================================
	#   0:00000000       1:00000554       2:00000969       3:00000CD3
	#   4:00000F80       5:00001849       6:00002292       7:00002967
	#   ...
	#  28:0002716E      29:00027192      30:00027210
	#
	elif (section["name"].startswith("Fixup Page Table")):
		decoded_data = OrderedDict()
		for line in section["data"]:
			line2 = str.join(" ", line.split())
			for data in line2.split(" "):
				data = data.split(":")
				if (len(data) != 2):
					logging.warning("invalid data: '%s'" % line2)
					continue
				decoded_data[int(data[0])] = int(data[1], 16)

	#                               Fixup Record Table
	# ==============================================================================
	# Source  Target
	#   type  flags
	#   ====  ====
	#    07    10   src off = 09B7   object #    = 02   target off       = 000498BA
	#    07    10   src off = 09FF   object #    = 02   target off       = 000498B0
	#    ...
	#    07    10   src off = 07DC   object #    = 01   target off       = 0003B2AC
	#
	# NOTE: not sure if source type, target flags and object # are decimal or hex; all decimal for now
	elif (section["name"].startswith("Fixup Record Table")):
		decoded_data = []
		for line in section["data"]:
			line2 = str.join(" ", line.split())

			match = re.match("^([0-9]+) ([0-9]+) src off = ([0-9a-fA-F ]+) object # = ([0-9]+) target off = ([0-9a-fA-F ]+)$", line2)
			if (match):
				decoded_data.append(OrderedDict([("source type", int(match.group(1))), ("target flags", int(match.group(2))), ("source offset", int(match.group(3), 16)), ("object", int(match.group(4))), ("target offset", int(match.group(5), 16))]))
				continue

			if (line2 == "Source Target" or line2 == "type flags" or line2 == "==== ===="):
				continue

			logging.warning("invalid data: '%s'" % line2)

	#                            Nonresident Names Table
	# ==============================================================================
	#
	# NOTE: not spotted with any data yet
	elif (section["name"].startswith("Nonresident Names Table")):
		decoded_data = str.join("", section["data"])

	#                               Master Debug Info
	# ==============================================================================
	# EXE major                 =       03H
	# EXE minor                 =       00H
	# ...
	#
	# Languages
	# =========
	# C
	# CPP
	#
	# Segments
	# ========
	# 0001
	# 0002
	#
	# Section 0 (off=000ABC09)
	# =========================
	#   Module info offset   = 00033BDEH
	#   Global info offset   = 000351FDH
	#   ...
	elif (section["name"].startswith("Master Debug Info")):
		decoded_data = OrderedDict()
		target = decoded_data
		for i in range(0, len(section["data"])):
			line = section["data"][i]
			line2 = str.join(" ", line.split())

			# Skip '='-only lines
			if (re.match("^[=]+$", line2)):
				continue

			# Handle subsections
			if (i < len(section["data"])-1 and re.match("^[=]+$", str.join(" ", section["data"][i+1].split()))):
				if (line2 == "Languages"):
					decoded_data["languages"] = []
					target = decoded_data["languages"]
					continue
				if (line2 == "Segments"):
					decoded_data["segments"] = []
					target = decoded_data["segments"]
					continue
				match = re.match("^Section ([0-9]+) \(off=([0-9a-fA-F]+)\)$", line2)
				if (match):
					if (not "sections" in decoded_data):
						decoded_data["sections"] = OrderedDict()
					num = int(match.group(1))
					decoded_data["sections"][num] = OrderedDict([("num", num), ("offset", int(match.group(2), 16))])
					target = decoded_data["sections"][num]
					continue

			# Decide how to append data based on target type
			if (isinstance(target, list)):
				target.append(line2)
			elif (isinstance(target, dict)):
				key, value = wdump_split_keyval(line2)
				if (key != None and value != None):
					target[key] = value
					continue
				logging.warning("invalid data: '%s'" % line2)

	#                            Module Info (section 0)
	# ==============================================================================
	#   0) Name:   D:\IBM\MKTRIL\SOURCE\input.c
	#      Language is C
	#      Locals: num = 1, offset = 00000012H
	#      Types:  num = 1, offset = 00000062H
	#      Lines:  num = 1, offset = 000000B2H
	#
	#    *** Locals ***
	#    ==============
	#       Data 0:  offset 00000236
	#         0000: MODULE_386
	#           "JoyThresholdY" addr = 0003:00059610,  type = 81
	#         0016: MODULE_386
	#           "JoyThresholdX" addr = 0003:00059618,  type = 82
	#         ...
	#         03BB: LOCAL
	#           address: BP_OFFSET_BYTE( C0 )
	#           name = "outregs",  type = 115
	#
	#    *** Line Numbers ***
	#    ====================
	#       1 offset entries:
	#         offset 0 = 00010894H
	#         offset 1 = 00010EEEH
	#       -------------------------------------
	#       Data 0: offset 00010894H, addr info off = 0000000EH, num = 32
	#         number =   93,  code offset = 00000008H
	#         number =  112,  code offset = 00000016H
	#         ...
	#         number =  172,  code offset = 0000019CH
	#       -------------------------------------
	#       Data 0: offset 00010894H, addr info off = 0000000EH, num = 32
	#         number =  174,  code offset = 000001A6H
	#         number =  176,  code offset = 000001BBH
	#         ...
	#
	#     *** Types ***
	#     =============
	#       Data 0:  offset 00007170
	#         0000: cue table offset=00000513
	#         0006: SCOPE(1)
	#           "struct"
	#         ...
	#         0509: NAME(115)
	#           "REGS"  type idx = 114  scope idx = 2
	#
	# NOTE: 'Types' appears after 'Line Numbers', contrary to order at beginning
	# NOTE: 'num' in this section means 'count', e.g. 'Lines:  num = 1, ...' means there's one 'Lines Numbers' section
	elif (section["name"].startswith("Module Info")):
		decoded_data = OrderedDict()
		current_module = None
		skip_until_next_module = False
		for line in section["data"]:
			line2 = str.join(" ", line.split())

			# Skip subsections '*** Locals ***', '*** Types ***' and '*** Line Numbers ***'
			if (line2 == "*** Locals ***" or line2 == "*** Types ***" or line2 == "*** Line Numbers ***"):
				skip_until_next_module = True
				continue

			# New module
			match = re.match("^([0-9]+)\) Name: (.+)$", line2)
			if (match):
				num = int(match.group(1))
				decoded_data[num] = OrderedDict([("num", num), ("name", match.group(2)), ("language", None), ("locals", OrderedDict()), ("types", OrderedDict()), ("lines", OrderedDict())])
				current_module = decoded_data[num]
				skip_until_next_module = False
				continue
			elif (skip_until_next_module):
				continue

			# Check if within module
			if (current_module == None):
				logging.warning("stray module data: '%s'" % line2)
				continue

			# Module data
			match = re.match("^Language is (.+)$", line2)
			if (match):
				current_module["language"] = match.group(1)
				continue
			match = re.match("^(.+): num = ([0-9]+), offset = ([0-9a-fA-F]+)H$", line2)
			if (match):
				key = match.group(1).lower()
				if (not key in current_module):
					logging.warning("invalid module data: '%s'" % line2)
					continue
				current_module[key]["count"] = int(match.group(2))
				current_module[key]["offset"] = int(match.group(3), 16)
				continue

			logging.warning("invalid data: '%s'" % line2)

	#                            Global Info (section 0)
	# ==============================================================================
	#   Name:  PackJoyButtons_
	#     address      = 0001:00000466
	#     module index = 0
	#     kind:          (code)
	#   Name:  _pTopOfHeap
	#     address      = 0003:0005983C
	#     module index = 100
	#     kind:          (static pubdef) (data)
	# NOTE: 'segment' here seems to correspond to 'object' for Linear Executables
	# NOTE: not exactly sure what global names like 'W?smp$n[]pn$_SAMPLE$$' mean; for sure is that name is between '?' and '$', i.e. 'smp' in this example
	elif (section["name"].startswith("Global Info")):
		decoded_data = []
		current_global = None
		for line in section["data"]:
			line2 = str.join(" ", line.split())

			# New global
			match = re.match("^Name: (.+)$", line2)
			if (match):
				name = match.group(1)
				match = re.match("^W\?([^$]+)\$", name)
				if (match):
					name = match.group(1)
				decoded_data.append(OrderedDict([("name", name), ("module", None), ("segment", None), ("offset", None), ("type", None)]))
				current_global = decoded_data[-1]
				continue

			# Check if within global
			if (current_global == None):
				logging.warning("stray global data: '%s'" % line2)
				continue

			# Global data
			match = re.match("^address = ([0-9]+):([0-9a-fA-F]+)$", line2)
			if (match):
				current_global["segment"] = int(match.group(1))
				current_global["offset"] = int(match.group(2), 16)
				continue
			match = re.match("^module index = ([0-9]+)$", line2)
			if (match):
				current_global["module"] = int(match.group(1))
				continue
			match = re.match("^kind: (.*)$", line2)
			if (match):
				if (match.group(1).endswith("(code)")):
					current_global["type"] = "code"
				elif (match.group(1).endswith("(data)")):
					current_global["type"] = "data"
				else:
					logging.warning("invalid global kind: '%s'" % line2)
					current_global["type"] = "unknown"
				continue

			logging.warning("invalid data: '%s'" % line2)

	#                             Addr Info (section 0)
	# ==============================================================================
	#  Base:  fileoff = 00000000H   seg = 0001H,  off = 00000000H
	#      0) fileoff = 00000008H,  Size = 00000010H @00000000H,  mod_index = 75
	#      1) fileoff = 0000000EH,  Size = 00003921H @00000010H,  mod_index = 0
	#      ...
	#  Base:  fileoff = 000003E0H   seg = 0002H,  off = 00000000H
	#      0) fileoff = 000003E8H,  Size = 00000004H @00000000H,  mod_index = 75
	#      1) fileoff = 000003EEH,  Size = 000006F0H @00000004H,  mod_index = 0
	#      ...
	# NOTE: '@[0-9a-fA-F]H' is offset of module within segment
	# NOTE: 'segment' here seems to correspond to 'object' for Linear Executables
	elif (section["name"].startswith("Addr Info")):
		decoded_data = []
		current_block = None
		for line in section["data"]:
			line2 = str.join(" ", line.split())

			# New block
			match = re.match("^Base: fileoff = ([0-9a-fA-F]+)H seg = ([0-9a-fA-F]+)H, off = ([0-9a-fA-F]+)H$", line2)
			if (match):
				decoded_data.append(OrderedDict([("file offset", int(match.group(1), 16)), ("segment", int(match.group(2), 16)), ("offset", int(match.group(3), 16)), ("entries", OrderedDict())]))
				current_block = decoded_data[-1]
				continue

			# Check if within block
			if (current_block == None):
				logging.warning("stray block data: '%s'" % line2)
				continue

			# Block data
			match = re.match("^([0-9]+)\) fileoff = ([0-9a-fA-F]+)H, Size = ([0-9a-fA-F]+)H @([0-9a-fA-F]+)H, mod_index = ([0-9]+)$", line2)
			if (match):
				num = int(match.group(1))
				#current_block["entries"][num] = OrderedDict([("num", num), ("file offset", int(match.group(2), 16)), ("size", int(match.group(3), 16)), ("size@", int(match.group(4), 16)), ("module", int(match.group(5)))])
				current_block["entries"][num] = OrderedDict([("num", num), ("file offset", int(match.group(2), 16)), ("size", int(match.group(3), 16)), ("offset", int(match.group(4), 16)), ("module", int(match.group(5)))])
				continue

			logging.warning("invalid data: '%s'" % line2)

	#                                  Object Hints
	# ==============================================================================
	#   Object 1:
	#     1) start = 00003931H, end = 00003939H, type = data, mode = dwords, comment = Presumably two DWORDs
	#     2) start = 0002CCFAH, end = 0002CD65H, type = data, mode = string, comment = Watcom copyright notice
	#     ...
	#     -or-
	#     1) offset = 00003931H, length = 00000008H, type = data, mode = dwords, comment = Presumably two DWORDs
	#     2) offset = 0002CCFAH, length = 0000006BH, type = data, mode = string, comment = Watcom copyright notice
	#     ...
	#   Object 2:
	#     1) start = 00000004H, end = 000006F4H, type = data, mode = strings, comment = Strings
	#     2) start = 000118B4H, end = 00011CB4H, type = data, mode = dwords, comment = Table of DWORDs
	#     ...
	#     -or-
	#     1) offset = 00000004H, length = 000006F0H, type = data, mode = strings, comment = Strings
	#     2) offset = 000118B4H, length = 00000400H, type = data, mode = dwords, comment = Table of DWORDs
	#     ...
	#   ...
	# NOTE: not native wdump, added specifically for wcdctool to support user-specified object hints to aid disassembly
	# NOTE: 'comment' has to be last (see special handling below)
	# NOTE: resulting items (dicts) will always have keys 'start', 'end' and 'length', no matter which format is used
	elif (section["name"].startswith("Object Hints")):
		decoded_data = OrderedDict()
		current_block = None
		for line in section["data"]:
			line2 = str.join(" ", line.split())

			# Comment
			if (line2.startswith("#")):
				continue

			# New block
			match = re.match("^Object ([0-9]+):$", line2)
			if (match):
				objnum = int(match.group(1))
				decoded_data[objnum] = (OrderedDict([("objnum", objnum), ("entries", OrderedDict())]))
				current_block = decoded_data[objnum]
				continue

			# Check if within block
			if (current_block == None):
				logging.warning("stray block data: '%s'" % line2)
				continue

			# Block data
			# x) start = ...H, end = ...H, type = ..., mode = ..., comment = ...
			match = re.match("^([0-9]+)\) start = ([0-9a-fA-F]+)H, end = ([0-9a-fA-F]+)H, type = (.+), mode = (.+?)(, .*)?$", line2)
			if (match):
				num = int(match.group(1))
				start = int(match.group(2), 16)
				end = int(match.group(3), 16)
				length = end - start
				type_ = match.group(4)
				mode = match.group(5)
				tail = match.group(6)
			else:
				# x) offset = ...H, length = ...H, type = ..., mode = ..., comment = ...
				match = re.match("^([0-9]+)\) offset = ([0-9a-fA-F]+)H, length = ([0-9a-fA-F]+)H, type = (.+), mode = (.+?)(, .*)?$", line2)
				if (match):
					num = int(match.group(1))
					start = int(match.group(2), 16)
					length = int(match.group(3), 16)
					end = start + length
					type_ = match.group(4)
					mode = match.group(5)
					tail = match.group(6)
			if (match):
				# Identify and store any key-value pairs found in tail
				keyvals = OrderedDict()
				if (tail != None):
					for item in tail.split(", "):
						if (item == ""):
							continue
						(key, value) = wdump_split_keyval(item)
						if (key == "comment"): # special handling of key 'comment': consume everything after '=' as value, break loop -> allows comments to contain ','
							match = re.search("comment = (.+)", tail)
							keyvals[key] = match.group(1)
							break
						elif (key != None and value != None):
							keyvals[key] = value
						else:
							logging.warning("invalid key-value pair '%s': '%s'" % (item, line2))

				# Sanity checks
				# NOTE: we check everything that is checkable at this point
				if (num in current_block["entries"]):
					logging.warning("invalid entry: entry with same num already exists: %s" % line2)
					continue
				if (end < start):
					logging.warning("invalid entry: invalid range (end < start): %s" % line2)
					continue
				if (type_ == "code"):
					if (not mode in ("default", "comment")):
						logging.warning("invalid entry: invalid mode '%s' for type '%s': '%s'" % (mode, type_, line2))
						continue
				elif (type_ == "data"):
					if (not mode in ("default", "comment", "auto-strings", "strings", "string", "bytes", "words", "dwords", "fwords", "qwords", "tbytes") and not mode.startswith("struct")):
						logging.warning("invalid entry: invalid mode '%s' for type '%s': '%s'" % (mode, type_, line2))
						continue
				else:
					logging.warning("invalid entry: invalid type '%s': '%s'" % (type_, line2))
					continue

				# Store entry
				current_block["entries"][num] = OrderedDict([("num", num), ("start", start), ("end", end), ("length", length), ("type", type_), ("mode", mode)] + list(keyvals.items()))
				continue

			logging.warning("invalid entry: '%s'" % line2)

	#                              <Unknown section>
	# ==============================================================================
	else:
		logging.warning("no decode rule for section '%s'" % section["name"])
		decoded_data = section["data"]


	# Replace section data with decoded data
	section["data"] = decoded_data

# Parses wdump output, returns parsed representation of output
def wdump_parse_output(input_file, wdump_exec, wdump_output, wdump_add_output, outfile_template):
	logging.info("")
	logging.info("Parsing wdump output:")

	# Obtain wdump output
	output = []
	if (wdump_output == None):
		# Run wdump as subprocess, fetch output (NOTE: order of wdump arguments is important, '-a', '-Dx' won't work!)
		logging.debug("Generating output for file '%s'..." % input_file)
		command = (wdump_exec, "-Dx", "-a", input_file)
		logging.debug("Running command '%s'..." % str.join(" ", command))
		try:
			sub_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
		except Exception as exception:
			logging.error("Error: %s" % str(exception))
			return None
		if (sub_process.returncode != 0):
			logging.error("Error: command failed with exit code %d:" % sub_process.returncode)
			logging.error(sub_process.stdout if (sub_process.stdout != "") else "<no output>")
			return None
		output = sub_process.stdout.splitlines()
		logging.debug("Writing plain output to file...")
		write_file(outfile_template % "wdump_output_plain.txt", output)
	else:
		# Read wdump output from file
		logging.debug("Reading output from file '%s'..." % wdump_output)
		try:
			with open(wdump_output, "r") as file:
				output = file.read().splitlines()
		except Exception as exception:
			logging.error("Error: %s" % str(exception))
			return None

	# Read additional wdump output from file
	if (wdump_add_output != None):
		logging.debug("Reading additional output from file '%s'..." % wdump_add_output)
		try:
			with open(wdump_add_output, "r") as file:
				output += file.read().splitlines()
		except Exception as exception:
			logging.error("Error: %s" % str(exception))
			return None

	# Process output, identify sections, distribute output to sections
	logging.debug("Processing output (%d lines)..." % len(output))
	sections = OrderedDict()
	current_section = None
	for i in range(0, len(output)):

		# Fetch line, create stripped copy (leading + inner + trailing whitespace)
		line = output[i]
		line2 = str.join(" ", line.split())

		# Skip empty/whitespace-only lines
		if (line2 == ""):
			continue

		# Skip '[=]{78}' lines (see below)
		if (re.match("^[=]{78}$", line2)):
			continue

		# New section (lookahead one line; if next line is '[=]{78}', then current line is name of new section)
		if (i < len(output)-1 and re.match("^[=]{78}$", str.join(" ", output[i+1].split()))):
			name = line2
			name2 = name.lower()
			sections[name2] = OrderedDict([("name", name), ("data", [])])
			current_section = sections[name2]
			continue

		# Report stray lines
		if (current_section == None):
			logging.warning("stray line: '%s'" % line)
			continue

		# Add original line to data of current section
		current_section["data"].append(line)

	# Print identified sections
	logging.info("Identified sections:")
	for section in sections:
		logging.debug(sections[section]["name"])

	# Decode section data
	logging.info("Decoding section data...")
	for section in sections:
		logging.debug("Section '%s'..." % sections[section]["name"])
		wdump_decode_data(sections[section])

	# Merge numbered sections, e.g. 'Module Info (section 0)' + 'Module Info (section 1)' -> sections["module info"]["data"] = OrderedDict([(0, <section 0>), (1, <section 1>)])
	# NOTE: using second variable here to avoid 'RuntimeError: OrderedDict mutated during iteration'; this is perfectly fine as we're only copying references around
	logging.info("Merging numbered sections...")
	sections2 = OrderedDict()
	for section in sections:
		match = re.match("^(.+) \(section ([0-9]+)\)$", sections[section]["name"])
		if (match):
			name = match.group(1)
			name2 = name.lower()
			num = int(match.group(2))
			if (not name2 in sections2):
				sections2[name2] = OrderedDict([("name", name), ("data", OrderedDict())])
			sections2[name2]["data"][num] = sections[section]
			logging.debug("Section '%s' -> '%s'..." % (sections[section]["name"], name))
		else:
			sections2[section] = sections[section]
	sections = sections2

	# Print final sections
	logging.info("Final sections:")
	for section in sections:
		logging.debug(sections[section]["name"])

	# Write parsed output to file
	logging.info("Writing parsed output to file...")
	write_file(outfile_template % "wdump_output_parsed.txt", format_pprint(sections))

	# Return results
	return sections
