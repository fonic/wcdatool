# Watcom Disassembly Tool (wcdatool)

Tool to aid disassembling DOS applications created with the *Watcom* toolchain.

## Watcom Toolchain

Many DOS applications of the 90s, especially games, were developed using the *Watcom* toolchain. Examples are *DOOM*, *Warcraft*, *Syndicate*, *Mortal Kombat*, just to name a few.

Most end-users probably never have heard of *Watcom*, but might remember applications displaying a startup banner reading something like this: `DOS/4G(W) Protected Mode Run-time [...]`. *DOS/4G(W)* was a popular DOS extender bundled with the *Watcom* toolchain.

Nowadays, the *Watcom* toolchain is open source and lives on as [Open Watcom](http://openwatcom.org/) / [Open Watcom v2 Fork](https://open-watcom.github.io/).

## Why create another disassembly tool?

The idea for this tool emerged when I discovered that one of my all-time favorite games, *Mortal Kombat*, was mainly written in Assembler (more or less directly ported from the arcade version) and, on top of that, released *unstripped* (i.e. with debug symbols kept intact). I tried using various decompilation/disassembly tools on it, only to discover that none seems to be capable of dealing with the specifics of *Watcom*-based applications.

Thus, I began writing my own tool. What originally started out as *mkdecomptool* specifically for *Mortal Kombat* is now the general-purpose *Watcom Disassembly Tool (wcdatool)*.

## Current state and future development

Wcdatool is *work in progress*. You can tell from looking at the source code - there's tons of TODO, TESTING, FIXME, etc. flying around. Also, it is relatively slow as performance has not been the main focus.

*Nevertheless, it works quite well in its current state* - you'll get a well-readable, reasonably structured disassembly output (*objdump* format).

Please note that the tool was mainly tested on *Mortal Kombat* executables, therefore results for other applications may vary greatly. If you come across other *unstripped* *Watcom*-based DOS applications that may be used for testing, please let me know.

The *next major goal* is to cleanly rewrite the disassembler module and transition from static code disassembly to branch tracing (e.g. *Mortal Kombat 2* executable contains code within its data object, which is currently neither discovered nor processed).

## How to use it

There are multiple ways to use *wcdatool*, but this should get you started:

1. Requirements:

   Wcdatool: *Python >= 3.6.0*, *wdump* (part of *Open Watcom*), *objdump* (part of [binutils](https://sourceware.org/binutils/))<br/>
   Open Watcom v2: *gcc* -or- *clang* (for 64-bit builds), *DOSEMU* -or- *DOSBox* (for *wgml* utility)<br/>

   **NOTE:** the following instructions assume *Open Watcom v2* is built from sources (the project also provides pre-compiled [binaries](https://github.com/open-watcom/open-watcom-v2/releases))

2. Download wcdatool:
   ```
   # git clone https://github.com/fonic/wcdatool.git
   ```

3. Download, build and install *Open Watcom v2*:
   ```
   # cd wcdatool/OpenWatcom
   # ./0_download.sh
   # ./1_build.sh
   # ./2_install_linux.sh /opt/openwatcom /opt/bin/openwatcom
   ```
   **NOTE:** these scripts are provided for convenience, they are not part of *Open Watcom v2* itself

4. Copy application executables to `wcdatool/Executables`, e.g. for *Mortal Kombat*:
   ```
   # cp <source-dir>/MK1.EXE wcdatool/Executables
   # cp <source-dir>/MK2.EXE wcdatool/Executables
   # cp <source-dir>/MK3.EXE wcdatool/Executables
   # cp <source-dir>/MKTRIL.EXE wcdatool/Executables
   ```
   **NOTE:** file names of executables are used to locate corresponding object hint files (see 5.)

5. Create/edit object hint files in `wcdatool/Hints` *(optional)*:

   Object hints may be used to manually affect the disassembly process (e.g. force decoding of certain regions as code/data, specify data decoding mode, define data structs, add comments). For now, please refer to included object hint files for *Mortal Kombat* for details regarding capabilites and syntax.

   **NOTE:** hint files are located and used automatically when stored as `wcdatool/Hints/<executable>.txt` (e.g. `wcdatool/Executables/MK1.EXE` -> `wcdatool/Hints/MK1.EXE.txt`)

6. Let *wcdatool* process all provided executables:
   ```
   # source /opt/bin/openwatcom
   # wcdatool/Scripts/process-all-executables.sh
   ```
   **NOTE:** for the executables listed in 4., this will take 5-10 min. and generate ~2.5 GB worth of data

7. Have a look at the results in `wcdatool/Output`, specifically:
   - files `<executable>_disasm_object_x_disassembly_plain.asm` contain plain disassembly
   - files `<executable>_disasm_object_x_disassembly_formatted.asm` contain formatted disassembly
   - folder `<executable>_modules` contains formatted disassembly split into separate modules <sup>(*)</sup>

   <sup>(*)</sup> *This attempts to reconstruct original source files (if corresponding debug info is available)*

## How to contact me

If you want to get in touch with me, give feedback, ask questions or simply need someone to talk to, please open an [Issue](https://github.com/fonic/wcdatool/issues) here on GitHub. Be sure to leave an email address if you prefer personal contact.
