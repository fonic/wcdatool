#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#                                                                         -
#  Watcom Disassembly Tool (wcdatool)                                     -
#  Module Pretty Print                                                    -
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 03/24/22                                              -
#                                                                         -
# -------------------------------------------------------------------------


# -------------------------------------
#                                     -
#  TODO                               -
#                                     -
# -------------------------------------

# - Extend 'format_pprint()':
#   - Add option 'hexdump_bytes=False'; if enabled, output hexdump of bytes
#     objects; output format (from Okteta; mark line, right-click, 'Copy As'
#     -> 'View in Plain Text'):
#
#     0000:F1E0 | 36 0F 02 6C  53 07 00 2B  0F 02 74 53  07 00 1D 0F | 6..lS..+..tS....
#     ^ 32-bit offset, simply split by ':' in the middle, i.e. two 16-bit words
#                 ^ hex 4 x 4 Bytes                                    ^ data in printable form (may contain '|') -> see 'is_ascii()', 'wcdctool_legacy.py'
#
# - Performance is not great, noticable when writing disassembly results to
#   files; try to improve performance


# -------------------------------------
#                                     -
#  Exports                            -
#                                     -
# -------------------------------------

__all__ = [ "format_pprint", "print_pprint" ]


# -------------------------------------
#                                     -
#  Imports                            -
#                                     -
# -------------------------------------

import sys


# -------------------------------------
#                                     -
#  Code                               -
#                                     -
# -------------------------------------

# Recursively generate pretty print of arbitrary objects
def format_pprint(obj, level_indent="  ", max_depth=None, verbose_output=True,
                  justify_output=True, prevent_loops=True, prevent_revisit=False,
                  explore_objects=True, excluded_ids=[], visited_ids=[],
                  path_ids=[], current_depth=0):
	"""Recursively generates pretty print of arbitrary objects.

	Recursively generates pretty print of contents of arbitrary objects. Contents
	are represented as lines containing key-value pairs. Recursion may be affected
	by various parameters (see below).

	Arguments:
	    max_depth:       Maximum allowed depth of recursion. If depth is exceeded,
	                     recursion is stopped.
	    verbose_output:  Produce verbose output. Adds some additional details for
	                     certain data types
	    justify_output:  Justify output. Produces output in block-like appearance
	                     with equal spacing between keys and values.
	    prevent_loops:   Detect and prevent recursion loops by keeping track of
	                     already visited objects within current recursion path.
	    prevent_revisit: Detect and prevent revisiting of already visited objects.
	                     While 'prevent_loops' prevents revisiting objects only
	                     within one single recursion path, this prevents revisiting
	                     objects globally across all recursion paths.
	    explore_objects: Explore (i.e. recurse into) arbitrary objects. If enabled,
	                     arbitrary objects not matching base types are explored.
	                     If disabled, only certain types of objects are explored
	                     (tuple, list, dict, set/frozenset). Note that this does
	                     not affect the initially provided object (which is always
	                     explored).
	    excluded_ids:    List of object IDs to exclude from exploration (i.e. re-
	                     cursion). Recursion is stopped if object with matching
	                     ID is encountered.
	    visited_ids,     Internal variables used to control recursion flow, loop
	    path_ids,        detection and revisit detection. Never provide or modify
	    current_depth:   these!

	Returns:
	    Generated pretty print output as list of lines (strings).

	Raises:
	    TypeError:       Object or value has unsupported type (should never occur)
	    AssertionError:  Assertion failed, most likely exposing a bug (should never
	                     occur)
	"""

	output = []
	indent = level_indent * current_depth

	# Check if object has already been visited within current recursion path.
	# If so, we encoutered a loop and thus need to break off recursion. If
	# not, continue and add object to list of visited objects within current
	# recursion path
	if (prevent_loops == True):
		if (id(obj) in path_ids):
			output.append(indent + "<recursion loop detected>")
			return output
		path_ids.append(id(obj))

	# Check if object has already been visited. If so, we're not going to visit
	# it again and break off recursion. If not, continue and add current object
	# to list of visited objects
	if (prevent_revisit == True):
		if (id(obj) in visited_ids):
			output.append(indent + "<item already visited>")
			return output
		visited_ids.append(id(obj))

	# Check if maximum allowed depth of recursion has been exceeded. If so, break
	# off recursion
	if (max_depth != None and current_depth > max_depth):
		output.append(indent + "<recursion limit reached>")
		return output

	# Check if object is supposed to be excluded. If so, break of recursion
	if (id(obj) in excluded_ids):
		output.append(indent + "<item is excluded>")
		return output

	# Determine keys and associated values
	if (isinstance(obj, dict)):
		keys = obj.keys()
		values = obj
	elif (isinstance(obj, tuple) or isinstance(obj, list)):
		keys = range(0, len(obj))
		values = obj
	elif (isinstance(obj, set) or isinstance(obj, frozenset)):
		keys = range(0, len(obj))
		values = [ item for item in obj ]
	elif (isinstance(obj, object)):
		keys = [ item for item in dir(obj) if (not item.startswith("_")) ]
		values = { key: getattr(obj, key) for key in keys }
	else: # should never occur as everything in Python is an 'object' and should be caught above
		raise TypeError("unsupported object type: '%s'" % type(obj))

	# Define key string templates. If output is to be justified, determine maximum
	# length of key string and adjust templates accordingly
	kstmp1 = kstmp2 = "%s"
	if (justify_output == True):
		maxlen = 0
		for key in keys:
			klen = len(str(key))
			if (klen > maxlen):
				maxlen = klen
		kstmp1 = "%-" + str(maxlen+3) + "s" # maxlen+3: surrounding single quotes + trailing colon
		kstmp2 = "%-" + str(maxlen+1) + "s" # maxlen+1: trailing colon

	# Process keys and associated values
	for key in keys:
		value = values[key]

		# Generate key string
		keystr = kstmp1 % ("'" + str(key) + "':") if (isinstance(obj, dict) and isinstance(key, str)) else kstmp2 % (str(key) + ":")

		# Generate value string
		valstr = ""
		exp_obj = False
		if (isinstance(value, dict)):
			valstr = "<dict, %d items, class '%s'>" % (len(value), type(value).__name__) if (verbose_output == True) else "<dict, %d items>" % len(value)
		elif (isinstance(value, tuple)):
			valstr = "<tuple, %d items, class '%s'>" % (len(value), type(value).__name__) if (verbose_output == True) else "<tuple, %d items>" % len(value)
		elif (isinstance(value, list)):
			valstr = "<list, %d items, class '%s'>" % (len(value), type(value).__name__) if (verbose_output == True) else "<list, %d items>" % len(value)
		elif (isinstance(value, set)): # set and frozenset are distinct
			valstr = "<set, %d items, class '%s'>" % (len(value), type(value).__name__) if (verbose_output == True) else "<set, %d items>" % len(value)
		elif (isinstance(value, frozenset)): # set and frozenset are distinct
			valstr = "<frozenset, %d items, class '%s'>" % (len(value), type(value).__name__) if (verbose_output == True) else "<frozenset, %d items>" % len(value)
		elif (isinstance(value, range)):
			valstr = "<range, start %d, stop %d, step %d>" % (value.start, value.stop, value.step) if (verbose_output == True) else "<range(%d,%d,%d)>" % (value.start, value.stop, value.step)
		elif (isinstance(value, bytes)):
			valstr = "<bytes, %d bytes>" % len(value)
		elif (isinstance(value, bytearray)):
			valstr = "<bytearray, %d bytes>" % len(value)
		elif (isinstance(value, memoryview)):
			valstr = "<memoryview, %d bytes, object %s>" % (len(value), type(value.obj).__name__) if (verbose_output == True) else "<memoryview, %d bytes>" % len(value)
		elif (isinstance(value, bool)): # needs to be above int as 'bool' also registers as 'int'
			valstr = "%s" % value
		elif (isinstance(value, int)):
			valstr = "%d (0x%x)" % (value, value)
		elif (isinstance(value, float)):
			valstr = "%s" % str(value) # str(value) provides best representation; alternatives: '%e|%E|%f|%F|%g|%G' % value
		elif (isinstance(value, complex)):
			valstr = "%s" % str(value)
		elif (isinstance(value, str)):
			#valstr = "%s" % repr(value) # using repr(value) to encode escape sequences (e.g. '\n' instead of actual newline); repr() adds surrounding quotes for strings (style based on contents)
			#valstr = "%r" % value # alternative, seems to be the same as repr(value)
			valstr = "'%s'" % repr(value)[1:-1] # this seems to be the only way to always get a single-quoted string
		elif (value == None):
			valstr = "None"
		elif isinstance(value, type): # checks if object is 'class' (https://stackoverflow.com/a/10123520/1976617); needs to be above 'callable' as 'class' also registers as 'callable'
			#valstr = "<class '%s'>" % type(value).__name__ if (verbose_output == True) else "<class>"
			valstr = "<class '%s.%s'>" % (value.__module__, value.__name__) if (verbose_output == True) else "<class>"
		elif (callable(value)): # catches everything callable, i.e. functions, methods, classes (due to constructor), etc.
			#valstr = "<callable, %s>" % repr(value)[1:-1] if (verbose_output == True) else "<callable>"
			#valstr = "<callable, class '%s'>" % type(value).__name__ if (verbose_output == True) else "<callable>"
			valstr = "<callable, class '%s.%s'>" % (value.__class__.__module__, value.__class__.__name__) if (verbose_output == True) else "<callable>"
		elif (isinstance(value, object)): # this has to be last in line as *everything* above also registers as 'object'
			#valstr = "<object, class '%s'>" % type(value).__name__ if (verbose_output == True) else "<object>"
			valstr = "<object, class '%s.%s'>" % (value.__class__.__module__, value.__class__.__name__) if (verbose_output == True) else "<object>"
			if (explore_objects == True):
				exp_obj = True # this ensures we only explore objects that do not represent a base type (i.e. everything listed above)
		else: # should never occur as everything in Python is an 'object' and should be caught above
			#valstr = "'%s'" % str(value) if (verbose_output == True) else str(value)
			raise TypeError("unsupported value type: '%s'" % type(value))

		# Generate key-value line from key/value strings and add to output
		output.append(indent + keystr + " " + valstr)

		# Explore value object recursively if it meets certain criteria
		if (isinstance(value, dict) or isinstance(value, tuple) or isinstance(value, list) or isinstance(value, set) or
		    isinstance(value, frozenset) or (isinstance(value, object) and exp_obj == True)):
			# These could be used to prevent recursion beforehand, i.e. before calling this
			# function again, as an alternative to checks at beginning of function. Leaving
			# this here for future reference
			#if (prevent_loops == True and id(value) in path_ids):
			#	#output[-1] += " <recursion loop detected>"
			#	output[-1] += " <recursion loop>"
			#	continue
			#if (prevent_revisit == True and id(value) in visited_ids):
			#	#output[-1] += " <item already visited>"
			#	output[-1] += " <already visited>"
			#	continue
			#if (max_depth != None and current_depth+1 > max_depth):
			#	#output[-1] += " <recusion limit reached>"
			#	output[-1] += " <recursion limit>"
			#	continue
			#if (id(value) in excluded_ids):
			#	#output[-1] += " <item is excluded>"
			#	output[-1] += " <item excluded>"
			#	continue
			output += format_pprint(value, level_indent=level_indent, max_depth=max_depth, verbose_output=verbose_output,
			                        justify_output=justify_output, prevent_loops=prevent_loops, prevent_revisit=prevent_revisit,
			                        explore_objects=explore_objects, excluded_ids=excluded_ids, visited_ids=visited_ids,
			                        path_ids=path_ids, current_depth=current_depth + 1)

		# TODO: hexdump of bytes and byte-like objects -> do it right here, no recursion
		#elif (isinstance(value, bytes) or isinstance(value, bytearray) or isinstance(value, memoryview)):
			# ...

	# Remove object from list of visited objects within current recursion path
	# (part of recursion loop detection; this 'rolls back' the laid out path)
	if (prevent_loops == True):
		assert len(path_ids) > 0 and path_ids[-1] == id(obj), "last item in list of path objects not existing or not matching object"
		path_ids.pop()

	# Return generated output
	return output

# Convenience wrapper for format_pprint()
def print_pprint(obj, *, file=sys.stdout, **kwargs):
	output = format_pprint(obj, **kwargs)
	output = str.join("\n", output)
	file.write(output + "\n")
	file.flush()
