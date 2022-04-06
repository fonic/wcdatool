#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#                                                                         -
#  Watcom Disassembly Tool (wcdatool)                                     -
#  Module Argument Parser                                                 -
#                                                                         -
#  Created by Fonic <https://github.com/fonic>                            -
#  Date: 06/20/19 - 08/18/20                                              -
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

__all__ = [ "ArgumentParser" ]


# -------------------------------------
#                                     -
#  Imports                            -
#                                     -
# -------------------------------------

import os
import sys
import argparse
import textwrap


# -------------------------------------
#                                     -
#  Code                               -
#                                     -
# -------------------------------------

# ArgumentParser class providing custom help/usage output
class ArgumentParser(argparse.ArgumentParser):

	# Postition of 'width' argument: https://www.python.org/dev/peps/pep-3102/
	def __init__(self, *args, width=78, **kwargs):
		# At least self.positionals + self.options need to be initialized before calling
		# __init__() of parent class, as argparse.ArgumentParser.__init__() defaults to
		# 'add_help=True', which results in call of add_argument("-h", "--help", ...)
		self.program = { key: kwargs[key] for key in kwargs }
		self.positionals = []
		self.options = []
		self.width = width
		super(ArgumentParser, self).__init__(*args, **kwargs)

	def add_argument(self, *args, **kwargs):
		super(ArgumentParser, self).add_argument(*args, **kwargs)
		argument = { key: kwargs[key] for key in kwargs }

		# Positional: argument with only one name not starting with '-' provided as
		# positional argument to method -or- no name and only a 'dest=' argument
		if (len(args) == 0 or (len(args) == 1 and isinstance(args[0], str) and not args[0].startswith("-"))):
			argument["name"] = args[0] if (len(args) > 0) else argument["dest"]
			self.positionals.append(argument)
			return

		# Option: argument with one or more flags starting with '-' provided as
		# positional arguments to method
		argument["flags"] = [ item for item in args ]
		self.options.append(argument)

	def format_usage(self):
		# Use user-defined usage message
		if ("usage" in self.program):
			prefix = "Usage: "
			wrapper = textwrap.TextWrapper(width=self.width)
			wrapper.initial_indent = prefix
			wrapper.subsequent_indent = len(prefix) * " "
			if (self.program["usage"] == "" or str.isspace(self.program["usage"])):
				return wrapper.fill("No usage information available")
			return wrapper.fill(self.program["usage"])

		# Generate usage message from known arguments
		output = []

		# Determine what to display left and right, determine string length for left
		# and right
		left1 = "Usage: "
		left2 = self.program["prog"] if ("prog" in self.program and self.program["prog"] != "" and not str.isspace(self.program["prog"])) else os.path.basename(sys.argv[0]) if (len(sys.argv[0]) > 0 and sys.argv[0] != "" and not str.isspace(sys.argv[0])) else "script.py"
		llen = len(left1) + len(left2)
		arglist = []
		for option in self.options:
			#arglist += [ "[%s]" % item if ("action" in option and (option["action"] == "store_true" or option["action"] == "store_false")) else "[%s %s]" % (item, option["metavar"]) if ("metavar" in option) else "[%s %s]" % (item, option["dest"].upper()) if ("dest" in option) else "[%s]" % item for item in option["flags"] ]
			flags = str.join("|", option["flags"])
			arglist += [ "[%s]" % flags if ("action" in option and (option["action"] == "store_true" or option["action"] == "store_false")) else "[%s %s]" % (flags, option["metavar"]) if ("metavar" in option) else "[%s %s]" % (flags, option["dest"].upper()) if ("dest" in option) else "[%s]" % flags ]
		for positional in self.positionals:
			arglist += [ "%s" % positional["metavar"] if ("metavar" in positional) else "%s" % positional["name"] ]
		right = str.join(" ", arglist)
		rlen = len(right)

		# Determine width for left and right parts based on string lengths, define
		# output template. Limit width of left part to a maximum of self.width / 2.
		# Use max() to prevent negative values. -1: trailing space (spacing between
		# left and right parts), see template
		lwidth = llen
		rwidth = max(0, self.width - lwidth - 1)
		if (lwidth > int(self.width / 2) - 1):
			lwidth = max(0, int(self.width / 2) - 1)
			rwidth = int(self.width / 2)
		#outtmp = "%-" + str(lwidth) + "s %-" + str(rwidth) + "s"
		outtmp = "%-" + str(lwidth) + "s %s"

		# Wrap text for left and right parts, split into separate lines
		wrapper = textwrap.TextWrapper(width=lwidth)
		wrapper.initial_indent = left1
		wrapper.subsequent_indent = len(left1) * " "
		left = wrapper.wrap(left2)
		wrapper = textwrap.TextWrapper(width=rwidth)
		right = wrapper.wrap(right)

		# Add usage message to output
		for i in range(0, max(len(left), len(right))):
			left_ = left[i] if (i < len(left)) else ""
			right_ = right[i] if (i < len(right)) else ""
			output.append(outtmp % (left_, right_))

		# Return output as single string
		return str.join("\n", output)

	def format_help(self):
		output = []
		dewrapper = textwrap.TextWrapper(width=self.width)

		# Add usage message to output
		output.append(self.format_usage())

		# Add description to output if present
		if ("description" in self.program and self.program["description"] != "" and not str.isspace(self.program["description"])):
			output.append("")
			output.append(dewrapper.fill(self.program["description"]))

		# Determine what to display left and right for each argument, determine max
		# string lengths for left and right
		lmaxlen = rmaxlen = 0
		for positional in self.positionals:
			positional["left"] = positional["metavar"] if ("metavar" in positional) else positional["name"]
		for option in self.options:
			if ("action" in option and (option["action"] == "store_true" or option["action"] == "store_false")):
				option["left"] = str.join(", ", option["flags"])
			else:
				option["left"] = str.join(", ", [ "%s %s" % (item, option["metavar"]) if ("metavar" in option) else "%s %s" % (item, option["dest"].upper()) if ("dest" in option) else item for item in option["flags"] ])
		for argument in self.positionals + self.options:
			if ("help" in argument and argument["help"] != "" and not str.isspace(argument["help"]) and "default" in argument and argument["default"] != argparse.SUPPRESS):
				argument["right"] = argument["help"] + " " + ( "(default: '%s')" % argument["default"] if isinstance(argument["default"], str) else "(default: %s)" % str(argument["default"]) )
			elif ("help" in argument and argument["help"] != "" and not str.isspace(argument["help"])):
				argument["right"] = argument["help"]
			elif ("default" in argument and argument["default"] != argparse.SUPPRESS):
				argument["right"] = "Default: '%s'" % argument["default"] if isinstance(argument["default"], str) else "Default: %s" % str(argument["default"])
			else:
				#argument["right"] = ""
				argument["right"] = "No description available"
			lmaxlen = max(lmaxlen, len(argument["left"]))
			rmaxlen = max(rmaxlen, len(argument["right"]))

		# Determine width for left and right parts based on maximum string lengths,
		# define output template. Limit width of left part to a maximum of self.width
		# / 2. Use max() to prevent negative values. -4: two leading spaces (indent)
		# + two trailing spaces (spacing between left and right), see template
		lwidth = lmaxlen
		rwidth = max(0, self.width - lwidth - 4)
		if (lwidth > int(self.width / 2) - 4):
			lwidth = max(0, int(self.width / 2) - 4)
			rwidth = int(self.width / 2)
		#outtmp = "  %-" + str(lwidth) + "s  %-" + str(rwidth) + "s"
		outtmp = "  %-" + str(lwidth) + "s  %s"

		# Wrap text for left and right parts, split into separate lines
		lwrapper = textwrap.TextWrapper(width=lwidth)
		rwrapper = textwrap.TextWrapper(width=rwidth)
		for argument in self.positionals + self.options:
			argument["left"] = lwrapper.wrap(argument["left"])
			argument["right"] = rwrapper.wrap(argument["right"])

		# Add positional arguments to output
		if (len(self.positionals) > 0):
			output.append("")
			output.append("Positionals:")
			for positional in self.positionals:
				for i in range(0, max(len(positional["left"]), len(positional["right"]))):
					left = positional["left"][i] if (i < len(positional["left"])) else ""
					right = positional["right"][i] if (i < len(positional["right"])) else ""
					output.append(outtmp % (left, right))

		# Add option arguments to output
		if (len(self.options) > 0):
			output.append("")
			output.append("Options:")
			for option in self.options:
				for i in range(0, max(len(option["left"]), len(option["right"]))):
					left = option["left"][i] if (i < len(option["left"])) else ""
					right = option["right"][i] if (i < len(option["right"])) else ""
					output.append(outtmp % (left, right))

		# Add epilog to output if present
		if ("epilog" in self.program and self.program["epilog"] != "" and not str.isspace(self.program["epilog"])):
			output.append("")
			output.append(dewrapper.fill(self.program["epilog"]))

		# Return output as single string
		return str.join("\n", output)

	# Method redefined as format_usage() does not return a trailing newline like
	# the original does
	def print_usage(self, file=None):
		if (file == None):
			file = sys.stdout
		file.write(self.format_usage() + "\n")
		file.flush()

	# Method redefined as format_help() does not return a trailing newline like
	# the original does
	def print_help(self, file=None):
		if (file == None):
			file = sys.stdout
		file.write(self.format_help() + "\n")
		file.flush()

	def error(self, message):
		sys.stderr.write(self.format_usage() + "\n")
		sys.stderr.write(("Error: %s" % message) + "\n")
		sys.exit(2)
