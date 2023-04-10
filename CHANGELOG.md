
Changelog for v3.0 release:

- added support for *TBYTES* (thanks to [halamix2](#12) for adding to this) (e.g. FATAL.EXE, PYL.EXE)

- implemented workaround for *fixup records lacking a target offset* (although not entirely sure what those are actually about) (e.g. FATAL.EXE, PYL.EXE)

- added support for *call/jump stubs* (i.e. call/jumps instructions with targets that only are determined at runtime via fixup records) (e.g. MK2.EXE)

- added *'fixup takes precedence' logic* for branch targets (i.e. fixups targets are considered more trustworthy and may override branch targets determined by objdump)

- added feature to *suggest possible object hints* for code objects (based on the observation that data regions in code objects usually get access sizes assigned to them)

- added preliminary support for a *branch tracing disassembler* (disabled by default, not ready for production yet)

- applied many additional *minor fixes/changes*
