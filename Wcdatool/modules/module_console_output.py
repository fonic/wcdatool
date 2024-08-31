#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#                                                                         -
#  Watcom Disassembly Tool (wcdatool)                                     -
#  Module Console Output                                                  -
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

__all__ = [ "get_ansi_mode", "set_ansi_mode", "print_text", "print_debug", "print_info", "print_warning", "print_error", "print_critical", "print_dark", "print_normal", "print_light", "print_hilite", "print_success", "print_good", "print_yes", "print_failure", "print_bad", "print_no", "set_window_title", "windows_enable_ansi_terminal", "windows_enter_to_exit" ]


# -------------------------------------
#                                     -
#  Imports                            -
#                                     -
# -------------------------------------

import sys
import io


# -------------------------------------
#                                     -
#  Code                               -
#                                     -
# -------------------------------------

# ANSI mode flag
ANSI_MODE = False

# Escape codes
ESC_STYLE = {
	"debug":    "\033[1;30m",
	"info":     "\033[0;37m",
	"warning":  "\033[1;33m",
	"error":    "\033[1;31m",
	"critical": "\033[1;35m",

	"dark":     "\033[1;30m",
	"normal":   "\033[0;37m",
	"light":    "\033[1m",
	"hilite":   "\033[1;36m",

	"success":  "\033[1;32m",
	"good":     "\033[1;32m",
	"yes":      "\033[1;32m",

	"failure":  "\033[1;31m",
	"bad":      "\033[1;31m",
	"no":       "\033[1;31m",
}
ESC_RESET = "\033[0m"
ESC_TITLE = "\033]0;%s\a"

# Get/set ANSI mode
def get_ansi_mode():
	return ANSI_MODE

def set_ansi_mode(enabled):
	if (not isinstance(enabled, bool)):
		raise TypeError("enabled must be type bool, not %s" % type(enabled).__name__)
	global ANSI_MODE
	ANSI_MODE = enabled

# Print text in specified style
# NOTE: function was designed to resemble Python's built-in print()
def print_text(*value, sep=" ", end="\n", file=sys.stdout, flush=True, style="normal"):
	if (not isinstance(sep, str)):
		raise TypeError("sep must be type str, not %s" % type(sep).__name__)
	if (not isinstance(end, str)):
		raise TypeError("end must be type str, not %s" % type(end).__name__)
	if (not isinstance(file, io.TextIOBase)):
		raise TypeError("file must be type io.TextIOBase, not %s" % type(file).__name__)
	if (not isinstance(flush, bool)):
		raise TypeError("flush must be type bool, not %s" % type(flush).__name__)
	if (not isinstance(style, str)):
		raise TypeError("style must be type str, not %s" % type(style).__name__)
	if (not style in ESC_STYLE):
		raise ValueError("invalid style: '%s'" % style)
	values = [ str(item) for item in value ]
	output = str.join(sep, values)
	#file.write(ESC_STYLE[style] + output + ESC_RESET + end if (ANSI_MODE == True) else output + end)
	file.write(ESC_STYLE[style] + output + ESC_RESET + end if (ANSI_MODE == True and output != "") else output + end)
	if (flush == True):
		file.flush()

# Convenience wrappers for print_text()
def print_debug(*args, **kwargs):
	print_text(*args, **kwargs, style="debug")

def print_info(*args, **kwargs):
	print_text(*args, **kwargs, style="info")

def print_warning(*args, **kwargs):
	print_text(*args, **kwargs, style="warning")

def print_error(*args, **kwargs):
	print_text(*args, **kwargs, style="error")

def print_critical(*args, **kwargs):
	print_text(*args, **kwargs, style="critical")

def print_dark(*args, **kwargs):
	print_text(*args, **kwargs, style="dark")

def print_normal(*args, **kwargs):
	print_text(*args, **kwargs, style="normal")

def print_light(*args, **kwargs):
	print_text(*args, **kwargs, style="light")

def print_hilite(*args, **kwargs):
	print_text(*args, **kwargs, style="hilite")

def print_success(*args, **kwargs):
	print_text(*args, **kwargs, style="success")

def print_good(*args, **kwargs):
	print_text(*args, **kwargs, style="good")

def print_yes(*args, **kwargs):
	print_text(*args, **kwargs, style="yes")

def print_failure(*args, **kwargs):
	print_text(*args, **kwargs, style="failure")

def print_bad(*args, **kwargs):
	print_text(*args, **kwargs, style="bad")

def print_no(*args, **kwargs):
	print_text(*args, **kwargs, style="no")

# Set window title
def set_window_title(title):
	if (ANSI_MODE == False):
		return
	sys.stdout.write(ESC_TITLE % title)
	sys.stdout.flush()

# Microsoft Windows: enable ANSI terminal (Windows 10 only; https://stack
# overflow.com/a/36760881/1976617, https://docs.microsoft.com/en-us/windows/
# console/setconsolemode)
def windows_enable_ansi_terminal():
	if (sys.platform == "win32"):
		try:
			import ctypes
			kernel32 = ctypes.windll.kernel32
			result = kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
			if (result == 0): raise Exception
			return True
		except:
			return False
	return None

# Microsoft Windows: prompt user to hit ENTER before continuing (similar to
# native 'pause' command; used before exiting to prevent window from closing
# prematurely; uses getpass to suppress any user input)
# NOTE:
# Checking if actually run from interactive terminal on Windows is non-trivial
# (would either require module 'psutil' or extensive ctypes magic; sys.stdout.
# isatty() is not much help as it is True on Windows when running via double-
# click); Thus, simply always prompt user, won't do any harm even if interactive
# NOTE:
# For some reason, output produced by getpass.getpass() will not be included
# when redirecting output, i.e. 'Hit ENTER to exit.' will always be displayed
# on the console. No idea why, but this is actually quite nice and useful :)
def windows_enter_to_exit():
	if (sys.platform == "win32"):
		try:
			import getpass
			getpass.getpass("\nHit ENTER to exit.")
			return True
		except:
			return False
	return None
