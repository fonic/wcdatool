## Changelog for v3.3 release

- fixed regression regarding *deduplication of consecutive data lines* (added in v3.2) messing up disassembly split into separate files (i.e. reconstructed source files) (fixes issue #16)
- prevent very long lines when deduplicating consecutive data lines by truncating hex output/display + appending '..'
- added support for regions with multiple access sizes when generating/outputting possible hints for code objects
- extended pretty printer (`modules/module_pretty_print.py`) to produce hex dumps of bytes and other bytes-like objects
- extended file writer (`module_miscellaneous.py`) to create folders for destination path if missing
- fixed regex strings in `re.match` and `re.search` calls producing `SyntaxWarning`s with Python 3.12+ due to invalid escape sequences (https://stackoverflow.com/a/52335971/1976617)
- applied various minor changes (console output, code formatting, comments, etc.)

## Changelog for v3.2 release

- added algorithm to *deduplicate consecutive data lines* in formatted disassembly (*greatly* reduces disassembly size for data objects)
- removed `TESTING` label for some code blocks that have proven themselves to be useful and stable
- applied minor updates to object hints (`MK2.EXE`, `PACMANVR.EXE`)

## Changelog for v3.1 release

- added algorithm to rename *duplicate globals* to avoid name clashing (unique labels are important/helpful when trying to recompile disassembly as one huge blob)
- added support for *loop instruction* (treated like call/jumps, i.e. loop targets contribute to branch analysis and are replaced with labels in formatted disassembly)
- added script to *compile wcdatool using Cython* (no performance gain yet as wcdatool's Python sources have not yet been decorated/optimized for Cython)
- fixed minor copy&paste mistake (references to non-existing variables in `module_miscellaneous.py`)
- updated object hints for *Pac-Man VR*
- overhauled a number of comments (clarification/updates/typos)
- added wcdatool's usage information to `README.md`
- applied a number of minor changes to `README.md`

## Changelog for v3.0 release

- added support for *TBYTES* (thanks to [halamix2](https://github.com/fonic/wcdatool/pull/12) for adding to this) (e.g. FATAL.EXE, PYL.EXE)
- implemented workaround for *fixup records lacking a target offset* (although not entirely sure what those are actually about) (e.g. FATAL.EXE, PYL.EXE)
- added support for *call/jump stubs* (i.e. call/jumps instructions with targets that only are determined at runtime via fixup records) (e.g. MK2.EXE)
- added *'fixup takes precedence' logic* for branch targets (i.e. fixups targets are considered more trustworthy and may override branch targets determined by objdump)
- added feature to *suggest possible object hints* for code objects (based on the observation that data regions in code objects usually get access sizes assigned to them)
- added preliminary support for a *branch tracing disassembler* (disabled by default, not ready for production yet)
- applied many additional *minor fixes/changes*

## Changelog for v2.0 release

- comprehensive rewrite of the entire tool:
  - no longer monolithic, sources now split into separate modules
  - disassembler now centered around fixup records
  - overhauled and verified almost all of the source code
- rebranded to 'wcdatool'

## Changelog for v1.0 release

- initial release
- monolithic (everything in one single source file)
- originally named 'wcdctool' (*Watcom Decompilation Tool*)

##

_Last updated: 08/31/24_
