#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#                                                                         -
#  Watcom Disassembly Tool (wcdatool)                                     -
#  Module Miscellaneous                                                   -
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 03/30/22                                              -
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

__all__ = [ "write_file", "dict_path_exists", "dict_path_value" ]


# -------------------------------------
#                                     -
#  Imports                            -
#                                     -
# -------------------------------------

import os


# -------------------------------------
#                                     -
#  Code                               -
#                                     -
# -------------------------------------

# Write content to file
# Accepted content: string, bytes, list of strings, list of bytes
def write_file(path, content, *, strings_separator=os.linesep, bytes_separator=b""):
	dir = os.path.dirname(path)
	try:
		if (dir != ""):
			os.makedirs(dir, exist_ok=True)
		if (isinstance(content, tuple) or isinstance(content, list)):
			if (len(content) > 0):
				if (isinstance(content[0], str)):
					with open(path, "wt") as file:
						file.write(str.join(strings_separator, content))
				elif (isinstance(content[0], bytes)):
					with open(path, "wb") as file:
						file.write(bytes.join(bytes_separator, content))
				else:
					raise TypeError("content has invalid type: '%s'" % type(content).__name__)
			else:
				with open(path, "w") as file:
					pass
		elif (isinstance(content, str)):
			with open(path, "wt") as file:
				file.write(content)
		elif (isinstance(content, bytes)):
			with open(path, "wb") as file:
				file.write(content)
		else:
			raise TypeError("content has invalid type: '%s'" % type(content).__name__)
	except Exception as exception:
		raise Exception("failed to write file '%s': %s" % (path, str(exception))) from exception

# Check if specified dictionary path exists (https://stackoverflow.com/a/43491315)
# Return value: True (if dict path exists), False (if dict path does not exist)
def dict_path_exists(dict_, *keys):
	if (not isinstance(dict_, dict)):
		raise TypeError("dict must be type dict, not %s" % type(sep).__name__)
	if (len(keys) == 0):
		raise IndexError("no key(s) specified")

	walker = dict_
	for key in keys:
		try:
			walker = walker[key]
		except KeyError:
			return False
	return True

# Get value of specified dictionary path
# Return value: value (if dict path exists), None (if dict path does not exist)
def dict_path_value(dict_, *keys):
	if (not isinstance(dict_, dict)):
		raise TypeError("dict must be type dict, not %s" % type(sep).__name__)
	if (len(keys) == 0):
		raise IndexError("no key(s) specified")

	walker = dict_
	for key in keys:
		try:
			walker = walker[key]
		except KeyError:
			return None
	return walker
