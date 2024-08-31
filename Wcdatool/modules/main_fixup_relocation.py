#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#                                                                         -
#  Watcom Disassembly Tool (wcdatool)                                     -
#  Main Part Fixup / Relocation                                           -
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 07/28/23                                              -
#                                                                         -
# -------------------------------------------------------------------------


# -------------------------------------
#                                     -
#  TODO                               -
#                                     -
# -------------------------------------

# - Nothing atm


# -------------------------------------
#                                     -
#  Exports                            -
#                                     -
# -------------------------------------

__all__ = [ "fixup_relocation_read_decode" ]


# -------------------------------------
#                                     -
#  Imports                            -
#                                     -
# -------------------------------------

import logging
from collections import OrderedDict
from modules.module_miscellaneous import *
from modules.module_pretty_print import *


# -------------------------------------
#                                     -
#  Code                               -
#                                     -
# -------------------------------------

# Get value of specified size from buffer
def fixup_get_value(buffer, offset, size, name=None, byteorder="little", signed=False):

	# Check bounds, raise exception if out of bounds
	# NOTE: we have to do this as slicing out of bounds will not raise exceptions; refer to:
	#       https://docs.python.org/3.6/library/stdtypes.html#sequence-types-list-tuple-range
	if (offset > len(buffer) or (offset + size) > len(buffer)):
		raise IndexError(name, size, len(buffer)-offset)

	# Convert bytes to value, advance offset
	value = int.from_bytes(buffer[offset:offset+size], byteorder=byteorder, signed=signed)
	offset += size

	# Return results
	return (value, offset)

# Get string of specified length from buffer
def fixup_get_string(buffer, offset, length, name=None, encoding="ascii"):

	# Check bounds, raise exception if out of bounds
	if (offset > len(buffer) or (offset + length) > len(buffer)):
		raise IndexError(name, length, len(buffer)-offset)

	# Decode string from bytes, advance offset
	string = bytes.decode(buffer[offset:offset+length], encoding=encoding)
	offset += length

	# Return results
	return (string, offset)

# Read and decode fixup/relocation data
# NOTE: we have to do this manually, i.e. by reading and decoding binary data directly from executable
#       as wdump does not provide all necessary information (specifically mapping of fixup records to
#       object pages)
# NOTE: based on document 'LX - Linear eXecutable Module Format Description - June 3, 1992'
#       [http://www.textfiles.com/programming/FORMATS/lxexe.txt]
#
# Fixup examples for MK1.EXE:
# ---------------------------
#
# Fixup record:
# 6535: <OrderedDict, 22 items>
#     'num':                        6535 (0x1987)
#     'page':                       30 (0x1e)
#     ...
#     'source object':              1 (0x1)
#     'source offset':              3511 (0xdb7)
#     'source offset 2':            122295 (0x1ddb7)
#     'target object':              2 (0x2)
#     'target offset':              150560 (0x24c20)
#
# Data in source object (in this case code):
# 1ddb6: b8 20 4c 02 00             mov    eax,0x24c20
#           ^ 0x1ddb7
#
# -> in object 1 (source object) at offset 0x1ddb7 (source offset), there is
#    a reference to object 2 (target object), offset 0x24c20 (target offset)
# -> when relocating, relocation offset for object 2 has to be added to value
#    0x24c20 stored at 0x1ddb7 in object 1
# -> e.g. object 2 relocation offset 0x12500:
#    0x24c20 + 0x12500 = 0x37120
#    1ddb6: b8 20 71 03 00          mov    eax,0x37120
# -> fixups work on binary data. Thus, it does not matter if source/target
#    objects carry code or data. In the example above, the fixup is applied
#    to code and the value to be 'fixed up' references data, but all other
#    combinations are possible as well, i.e. code-code, code-data, data-code,
#    data-data.
#
# Fixups at page boundaries:
# For fixups at page boundaries, there will always be two identical records,
# one for each side of the boundary (only source offset is different). Note
# the negative offsets (relative to page) on the second record of each pair:
# Page 25, record: 5371, source object: 1, source offset: 0xffe, source offset 2: 0x18ffe, target object: 2, target offset: 0x44480
# Page 26, record: 5793, source object: 1, source offset: 0x-2,  source offset 2: 0x18ffe, target object: 2, target offset: 0x44480
# Page 31, record: 6729, source object: 1, source offset: 0xffd, source offset 2: 0x1effd, target object: 2, target offset: 0x24b5c
# Page 32, record: 7008, source object: 1, source offset: 0x-3,  source offset 2: 0x1effd, target object: 2, target offset: 0x24b5c
# Page 40, record: 7399, source object: 1, source offset: 0xfff, source offset 2: 0x27fff, target object: 2, target offset: 0x5a874
# Page 41, record: 7879, source object: 1, source offset: 0x-1,  source offset 2: 0x27fff, target object: 2, target offset: 0x5a874
#
# -> for each pair, always record for page[i] + record for page[i+1]
# -> for each pair, always same distance of source offsets to boundary
#
# NOTE:
# 'source offset' is relative to the parent page of a fixup record (signed
# 16 bit value). Since this is not of much use later on, 'source offset 2'
# is calculated and stored for each record (unsigned 32 bit value; relative
# to object, i.e. basically 'absolute')
#
def fixup_relocation_read_decode(wdump, input_file, outfile_template):
	logging.info("")
	logging.info("Reading and decoding fixup/relocation data:")

	# Sanity checks
	if (not dict_path_exists(wdump, "linear exe header (os/2 v2.x) - le", "data", "file offset") or
	    not dict_path_exists(wdump, "linear exe header (os/2 v2.x) - le", "data", "fixup section size") or
	    not dict_path_exists(wdump, "linear exe header (os/2 v2.x) - le", "data", "offset of fixup page table") or
	    not dict_path_exists(wdump, "linear exe header (os/2 v2.x) - le", "data", "offset of fixup record table") or
	    not dict_path_exists(wdump, "linear exe header (os/2 v2.x) - le", "data", "offset of import module name table") or
	    not dict_path_exists(wdump, "linear exe header (os/2 v2.x) - le", "data", "offset of import procedure name table")):
		logging.error("Error: fixup/relocation data not found in wdump data")
		return None

	# Storage for results
	fixup = OrderedDict()

	# Determine fixup tables offsets/sizes
	logging.debug("Determining fixup tables offsets/sizes...")
	section = wdump["linear exe header (os/2 v2.x) - le"]["data"]
	fixup["offset page table"] = section["offset of fixup page table"]
	fixup["offset record table"] = section["offset of fixup record table"]
	fixup["offset module table"] = section["offset of import module name table"]
	fixup["offset procedure table"] = section["offset of import procedure name table"]
	fixup["file offset page table"] = section["file offset"] + section["offset of fixup page table"]
	fixup["file offset record table"] = section["file offset"] + section["offset of fixup record table"]
	fixup["file offset module table"] = section["file offset"] + section["offset of import module name table"]
	fixup["file offset procedure table"] = section["file offset"] + section["offset of import procedure name table"]
	fixup["size page table"] = section["offset of fixup record table"] - section["offset of fixup page table"]
	fixup["size record table"] = section["offset of import module name table"] - section["offset of fixup record table"]
	fixup["size module table"] = section["offset of import procedure name table"] - section["offset of import module name table"]
	fixup["size procedure table"] = section["offset of fixup page table"] + section["fixup section size"] - section["offset of import procedure name table"]
	fixup["size total"] = section["fixup section size"]

	# Read fixup data from input file
	fixup["data page table"] = b""
	fixup["data record table"] = b""
	fixup["data module table"] = b""
	fixup["data procedure table"] = b""
	fixup["data total"] = b""
	try:
		logging.debug("Opening input file to read data...")
		with open(input_file, "rb") as infile:
			logging.debug("Seeking to offset 0x%x..." % fixup["file offset page table"])
			infile.seek(fixup["file offset page table"])
			logging.debug("Reading fixup data...")
			fixup["data total"] = infile.read(fixup["size total"])
			if (len(fixup["data total"]) != fixup["size total"]):
				logging.warning("Fixup data length does not match size (expected %d bytes, got %d bytes)" % (fixup["size total"], len(fixup["data total"])))
	except Exception as exception:
		logging.error("Error: %s" % str(exception))
		return None

	# Write fixup data to output file
	logging.debug("Writing fixup data to file (%d bytes)..." % len(fixup["data total"]))
	write_file(outfile_template % "fixup_data_binary.bin", fixup["data total"])

	# Slice fixup data into table data
	for table in ("page", "record", "module", "procedure"):
		fixup["data %s table" % table] = fixup["data total"][fixup["offset %s table" % table]-fixup["offset page table"]:fixup["offset %s table" % table]-fixup["offset page table"]+fixup["size %s table" % table]]
		if (len(fixup["data %s table" % table]) != fixup["size %s table" % table]):
			logging.warning("%s table data length does not match size (expected %d bytes, got %d bytes)" % (table.capitalize(), fixup["size %s table" % table], len(fixup["data %s table" % table])))
	if (len(fixup["data page table"]) + len(fixup["data record table"]) + len(fixup["data module table"]) + len(fixup["data procedure table"]) != fixup["size total"]):
		logging.warning("Sum of table data lengths does not match fixup data total size (expected %d bytes, got %d bytes)" % (fixup["size total"], len(fixup["data page table"]) + len(fixup["data record table"]) + len(fixup["data module table"]) + len(fixup["data procedure table"])))

	# Decode fixup page table data
	# NOTE: fixup page table is array of 32 bit values which specify offsets of fixup records data in fixup record table, e.g.
	#       0: 0x0, 1: 0x554, 2: 0x969, ... -> records for page 0 are stored in bytes 0x0..0x553 of record table data, entries
	#       for page 1 in bytes 0x554..0x968, ...
	# NOTE: by design, an additional entry (the last one) indicates end of fixup record table to facilitate offset calculation
	#       mechanism (see for-loop below)
	logging.debug("Decoding fixup page table...")
	values = []
	offset = 0
	while (offset < len(fixup["data page table"])):
		try:
			(value, offset) = fixup_get_value(fixup["data page table"], offset, 4, "value")
			if (len(values) > 0 and value < values[-1]):
				logging.warning("Current value %d (0x%x) is less than last value %d (0x%x), aborting decode" % (value, value, values[-1], values[-1]))
				break
			if (value > len(fixup["data record table"])):
				logging.warning("Value %d (0x%x) is out of bounds, aborting decode" % (value, value))
				break
			values.append(value)
		except IndexError as indexerror:
			logging.warning("Failed to read next %s (need %d bytes, left %d bytes), aborting decode" % (indexerror.args[0], indexerror.args[1], indexerror.args[2]))
			break

	# Construct fixup page table
	# NOTE: as page table data is array of 32 bit offset, we need value[i] & value[i+1] for calculation in each iteration
	fixup["page table"] = OrderedDict()
	page_num = 1
	for i in range(0, len(values)-1):
		fixup["page table"][page_num] = OrderedDict([("num", page_num), ("offset start", values[i]), ("offset end", values[i+1]), ("size", values[i+1]-values[i])])
		page_num += 1

	# Decode fixup record table data, construct fixup record table
	# NOTE: record table entries have variable sizes depending on certain bits in first two bytes of each entry
	logging.debug("Decoding fixup record table...")
	fixup["record table"] = OrderedDict()
	record_num = 1
	for pte in fixup["page table"].values():

		# Slice record data for current page
		pte["data"] = fixup["data record table"][pte["offset start"]:pte["offset end"]]
		if (len(pte["data"]) != pte["size"]):
			logging.warning("Page %d record data length does not match size (expected %d bytes, got %d bytes)" % (i, pte["size"], len(pte["data"])))

		# Decode record data for current page
		pte["records"] = OrderedDict()
		offset = 0
		while (offset < len(pte["data"])):
			try:
				# New record table entry
				rte = OrderedDict([("num", record_num), ("page", pte["num"]), ("offset start", offset), ("offset end", offset), ("size", 0)])

				# Read and decode flags bytes											# two bytes: one byte source flags, one byte target flags
				(rte["source flags"], offset) = fixup_get_value(pte["data"], offset, 1, "source flags")
				rte["source flags type"] = rte["source flags"] & 0x0f					# mask -> value 0x00..0x08
				rte["source flags alias"] = (rte["source flags"] >> 4) & 0x01			# flag -> if set, source refers to 16:16 alias
				rte["source flags list"] = (rte["source flags"] >> 5) & 0x01			# flag -> if set, source offset field is byte containing number of source offsets, list of source offsets follows end of record (after optional additive value)

				(rte["target flags"], offset) = fixup_get_value(pte["data"], offset, 1, "target flags")
				rte["target flags type"] = rte["target flags"] & 0x03					# mask -> value 0x00..0x03
				rte["target flags additive"] = (rte["target flags"] >> 2) & 0x01		# flag -> if set, additive value follows end of record (before optional source offset list)
				rte["target flags reserved"] = (rte["target flags"] >> 3) & 0x01		# flag -> must be zero
				rte["target flags offset type"] = (rte["target flags"] >> 4) & 0x01		# flag -> if set, target offset is 32 bits, otherwise 16 bits
				rte["target flags additive type"] = (rte["target flags"] >> 5) & 0x01	# flag -> if set, additive value is 32 bits, otherwise 16 bits
				rte["target flags obj/mod type"] = (rte["target flags"] >> 6) & 0x01	# flag -> if set, object number / module ordinal is 16 bits, otherwise 8 bits
				rte["target flags ordinal type"] = (rte["target flags"] >> 7) & 0x01	# flag -> if set, ordinal number is 8 bits, otherwise 16 bits

				# Add source object number
				rte["source object"] = None												# not part of record data, will be filled when processing objects/pages/segments below; initialized here for dict order

				# Read source offset field												# either byte containing number of source offset list entries or word (16 bits) containing source offset (NOTE: offset is signed!)
				if (rte["source flags list"] == 1):
					rte["source offset list"] = OrderedDict()							# will be filled after 'read target data'; initialized here for dict order
					rte["source offset list 2"] = OrderedDict()							# not part of record data, will be filled when processing objects/pages/segments below; initialized here for dict order
					(rte["source offset list length"], offset) = fixup_get_value(pte["data"], offset, 1, "source offset list length")
				else:
					(rte["source offset"], offset) = fixup_get_value(pte["data"], offset, 2, "source offset", signed=True)
					rte["source offset 2"] = None										# not part of record data, will be filled when processing objects/pages/segments below; initialized here for dict order

				# Read target data														# variable contents and sizes depending on target flags
				if (rte["target flags type"] == 0x00):									# 0x00h = Internal reference
					(rte["target object"], offset) = fixup_get_value(pte["data"], offset, 2, "target object") if (rte["target flags obj/mod type"] == 1) else fixup_get_value(pte["data"], offset, 1, "target object")
					if (rte["source flags type"] != 0x02):								# 0x02h = 16-bit selector fixup
						(rte["target offset"], offset) = fixup_get_value(pte["data"], offset, 4, "target offset") if (rte["target flags offset type"] == 1) else fixup_get_value(pte["data"], offset, 2, "target offset")
				elif (rte["target flags type"] == 0x01):								# 01h = Imported reference by ordinal (NOTE: might be swapped with 0x02, documentation unclear on this)
					logging.warning("First time target flags type %d (0x%x) is encountered, testing/debugging required" % (rte["target flags type"], rte["target flags type"]))
					(rte["target module ordinal"], offset) = fixup_get_value(pte["data"], offset, 2, "target module ordinal") if (rte["target flags obj/mod type"] == 1) else fixup_get_value(pte["data"], offset, 1, "target module ordinal")
					(rte["target procedure name offset"], offset) = fixup_get_value(pte["data"], offset, 4, "target procedure name offset") if (rte["target flags offset type"] == 1) else fixup_get_value(pte["data"], offset, 2, "target procedure name offset")
					if (rte["target flags additive"] == 1):
						(rte["target additive value"], offset) = fixup_get_value(pte["data"], offset, 4, "target additive value") if (rte["target flags additive type"] == 1) else fixup_get_value(pte["data"], offset, 2, "target additive value")
				elif (rte["target flags type"] == 0x02):								# 02h = Imported reference by name (NOTE: might be swapped with 0x01, documentation unclear on this)
					logging.warning("First time target flags type %d (0x%x) is encountered, testing/debugging required" % (rte["target flags type"], rte["target flags type"]))
					(rte["target module ordinal"], offset) = fixup_get_value(pte["data"], offset, 2, "target module ordinal") if (rte["target flags obj/mod type"] == 1) else fixup_get_value(pte["data"], offset, 1, "target module ordinal")
					(rte["target import ordinal"], offset) = fixup_get_value(pte["data"], offset, 1, "target import ordinal") if (rte["target flags ordinal type"] == 1) else fixup_get_value(pte["data"], offset, 4, "target import ordinal") if (rte["target flags offset type"] == 1) else fixup_get_value(pte["data"], offset, 2, "target import ordinal")
					if (rte["target flags additive"] == 1):
						(rte["target additive value"], offset) = fixup_get_value(pte["data"], offset, 4, "target additive value") if (rte["target flags additive type"] == 1) else fixup_get_value(pte["data"], offset, 2, "target additive value")
				elif (rte["target flags type"] == 0x03):								# 03h = Internal reference via entry table
					logging.warning("First time target flags type %d (0x%x) is encountered, testing/debugging required" % (rte["target flags type"], rte["target flags type"]))
					(rte["target entry ordinal"], offset) = fixup_get_value(pte["data"], offset, 2, "target entry ordinal") if (rte["target flags obj/mod type"] == 1) else fixup_get_value(pte["data"], offset, 1, "target entry ordinal")
					if (rte["target flags additive"] == 1):
						(rte["target additive value"], offset) = fixup_get_value(pte["data"], offset, 4, "target additive value") if (rte["target flags additive type"] == 1) else fixup_get_value(pte["data"], offset, 2, "target additive value")
				else:
					logging.warning("Page %d, record %d: invalid target type: %d (0x%x), aborting decode" % (pte["num"], record_num, rte["target flags type"], rte["target flags type"]))
					break

				# Read source offset list												# list of words (16 bits), only present if corresponding flag in source flags is set (NOTE: offsets are signed!)
				if (rte["source flags list"] == 1):
					rte["source offset list"] = OrderedDict()
					for i in range(1, rte["source offset list length"]+1):
						(rte["source offset list"][i], offset) = fixup_get_value(pte["data"], offset, 2, "source offset list entry %d" % i, signed=True)

				# Calculate end/size
				rte["offset end"] = offset
				rte["size"] = rte["offset end"] - rte["offset start"]

				# Store record table entry
				fixup["record table"][record_num] = rte
				pte["records"][record_num] = rte
				record_num += 1

			except IndexError as indexerror:
				logging.warning("Page %d, record %d: failed to read %s (need %d bytes, left %d bytes), aborting decode" % (pte["num"], record_num, indexerror.args[0], indexerror.args[1], indexerror.args[2]))
				break

	# Process fixup records and calculate source offset(s) relative to parent object
	# NOTE: we do this because source offsets in fixup records are by design relative to their parent page, which is of no
	#       use to us in the further process
	# NOTE: pages are already numbered correctly in wdump data, e.g. object 1 has pages numbered 1..60, object 2 has pages
	#       numbered  61..130 -> page["num"] can be used
	logging.debug("Calculating source offsets relative to parent object...")
	if (dict_path_exists(wdump, "object table", "data")):
		for object in wdump["object table"]["data"].values():
			if (not "pages" in object):
				logging.warning("Object %d has no pages" % (object["num"]))
				continue
			object_offset = 0
			for page in object["pages"].values():
				if (dict_path_exists(fixup, "page table", page["num"], "records")):
					for rte in fixup["page table"][page["num"]]["records"].values():
						rte["source object"] = object["num"]
						if ("source offset" in rte):
							rte["source offset 2"] = rte["source offset"] + object_offset
						if ("source offset list" in rte):
							rte["source offset list 2"] = OrderedDict()
							for i in range(1, len(rte["source offset list"])+1):
								rte["source offset list 2"][i] = rte["source offset list"][i] + object_offset
				else:
					logging.warning("Object %d page %d has no fixup records" % (object["num"], page["num"]))
				if (not "segments" in page):
					logging.warning("Object %d page %d has no segments" % (object["num"], page["num"]))
					continue
				for segment in page["segments"].values():
					if (not "data" in segment):
						logging.warning("Object %d page %d segment %d has no data" % (object["num"], page["num"], segment["num"]))
						continue
					object_offset += len(segment["data"])
	else:
		logging.warning("Object table empty, skipping calculation")

	# Decode import module/procedure name table data (NOTE: needs testing/debugging, no real data to test with yet)
	for table in ("module", "procedure"):
		logging.debug("Decoding import %s name table..." % table)
		fixup["%s table" % table] = OrderedDict()
		string_num = 1
		offset = 0
		while (offset < len(fixup["data %s table" % table])):
			try:
				(length, offset) = fixup_get_value(fixup["data %s table" % table], offset, 1, "string length")
				if (length == 0):
					logging.warning("String %d is empty" % string_num)
				if (length > 127):
					logging.warning("String %d is longer than 127 characters" % string_num)
				(string, offset) = fixup_get_string(fixup["data %s table" % table], offset, length, "string")
				fixup["%s table" % table][string_num] = string
				string_num += 1
			except IndexError as indexerror:
				logging.warning("Failed to read next %s (need %d bytes, left %d bytes), aborting decode" % (indexerror.args[0], indexerror.args[1], indexerror.args[2]))
				break

	# Write results to file
	output = format_pprint(fixup)
	logging.debug("Writing decoded data to file (%d lines)..." % len(output))
	write_file(outfile_template % "fixup_data_decoded.txt", output)

	# Return results
	return fixup
