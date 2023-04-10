# Watcom Disassembly Tool (wcdatool)

Tool to aid disassembling DOS applications created with the *Watcom* toolchain.

## Watcom Toolchain

Many DOS applications of the 90s, especially games, were developed using the *Watcom* toolchain. Examples are *DOOM*, *Warcraft*, *Syndicate*, *Mortal Kombat*, just to name a few.

Most end-users probably never have heard of *Watcom*, but might remember applications displaying a startup banner reading something like this: `DOS/4G(W) Protected Mode Run-time [...]`. *DOS/4G(W)* was a popular DOS extender bundled with the *Watcom* toolchain, allowing DOS applications to run in *32-bit protected mode*.

Nowadays, the *Watcom* toolchain is open source and lives on as [Open Watcom](http://openwatcom.org/) / [Open Watcom v2 Fork](https://open-watcom.github.io/).

## Why create another disassembly tool?

The idea for this tool emerged when I discovered that one of my all-time favorite games, *Mortal Kombat*, was mainly written in Assembler (more or less directly ported from the arcade version) and was released *unstripped* (i.e. executable contains debug symbols). I tried using various decompilation/disassembly tools on it, only to discover that none seemed to be capable of dealing with the specifics of *Watcom*-based applications.

Thus, I began writing my own tool. What originally started out as *mkdecomptool* specifically for *Mortal Kombat* is now the general-purpose *Watcom Disassembly Tool (wcdatool)*.

## Current state and future development

Wcdatool is *work in progress*. You can tell from looking at the source code - there's tons of TODO, TESTING, FIXME, etc. flying around. Also, it is relatively slow as performance has not been the main focus.

*Nevertheless, it works quite well in its current state* - you'll get a well-readable, reasonably structured disassembly output (*objdump* format). Check out issues [#9](https://github.com/fonic/wcdatool/issues/9) and [#11](https://github.com/fonic/wcdatool/issues/11) for games other than *Mortal Kombat* that wcdatool worked nicely for thus far.

**Please note that wcdatool works best when used on executables that contain debug symbols.** If you come across other *unstripped* *Watcom*-based DOS applications that may be used for further testing and development, please let me know.

The *next major goal* is to cleanly rewrite the disassembler module and transition from static code disassembly to branch tracing (e.g. *Mortal Kombat 2* executable contains code within its data object, which is currently neither discovered nor processed).

## How to use it

There are multiple ways to use *wcdatool*, but the following instructions should get you started. These instructions assume that you are using *Linux*. For *Windows* users, the easiest way to go is to use *Windows Subsystem for Linux (WSL)*:

1. Requirements:

   Wcdatool: *Python >= 3.6.0*, *wdump* (part of [Open Watcom v2](https://open-watcom.github.io/)), *objdump* (part of [binutils](https://sourceware.org/binutils/))<br/>
   (both *wdump* and *objdump* need to be accessible via `PATH`)

   Open Watcom v2: *gcc* -or- *clang* (for 64-bit builds), *DOSEMU* -or- *DOSBox* (for *wgml* utility)<br/>
   (only relevant if *Open Watcom v2* is built from sources; the project also provides [pre-compiled binaries](https://github.com/open-watcom/open-watcom-v2/releases))

2. Clone *wcdatool*'s repository (-or- download and extract a [release](https://github.com/fonic/wcdatool/releases)):
   ```
   # git clone https://github.com/fonic/wcdatool.git
   ```

3. Download, build and install *Open Watcom v2* (-or- download and install [pre-compiled binaries](https://github.com/open-watcom/open-watcom-v2/releases)):
   ```
   # cd wcdatool/OpenWatcom
   # ./1_download.sh
   # ./2_build.sh
   # ./3_install_linux.sh /opt/openwatcom /opt/bin/openwatcom
   ```
   **NOTE:** these scripts are provided for convenience, they are not part of the *Open Watcom v2* project itself

4. Copy the executables to be disassembled to `wcdatool/Executables`, e.g. for *Mortal Kombat*:
   ```
   # cp <source-dir>/MK1.EXE wcdatool/Executables
   # cp <source-dir>/MK2.EXE wcdatool/Executables
   # cp <source-dir>/MK3.EXE wcdatool/Executables
   ```
   **NOTE:** file names of executables are used to locate corresponding object hint files (see step 5)

5. Create/update object hint files in `wcdatool/Hints` *(optional; skip when just getting started)*:

   Object hints may be used to manually affect the disassembly process (e.g. force decoding of certain regions as code/data, specify data decoding mode, define data structs, add comments). Please refer to included object hint files for *Mortal Kombat*, *Fatal Racing* and *Pac-Man VR* for details regarding capabilites and syntax.

   **NOTE:** hint files must be stored as `wcdatool/Hints/<name-of-executable>.txt` (case-sensitive, e.g. `wcdatool/Executables/MK1.EXE` -> `wcdatool/Hints/MK1.EXE.txt`) to be picked up automatically by the included scripts

6. Let *wcdatool* process all provided executables (for the executables listed in step 4, this will take ~4min. and generate ~2GB worth of data):
   ```
   # wcdatool/Scripts/process-all-executables.sh
   ```

   -or- Let *wcdatool* process a single executable:
   ```
   # wcdatool/Scripts/process-single.executable.sh <name-of-executable>
   ```

   -or- Run *wcdatool* manually (use `--help` to display detailed usage information):
   ```
   # python wcdatool/Wcdatool/wcdatool.py -od wcdatool/Output -wao wcdatool/Hints/<name-of-executable>.txt wcdatool/Executables/<name-of-executable>
   ```

   **NOTE:** it is completely normal and expected for *wcdatool* to produce LOTS of warnings; ignore those when just getting started (see step 8 for details)

7. Have a look at the results in `wcdatool/Output`:
   - File `<name-of-executable>_zzz_log.txt` contains *log messages* (same as console output, but without coloring/formatting)
   - Files `<name-of-executable>_disasm_object_x_disassembly_plain.asm` contain *plain disassembly*
   - Files `<name-of-executable>_disasm_object_x_disassembly_formatted.asm` contain *formatted disassembly*
   - Folder `<name-of-executable>_modules` contains *formatted disassembly split into separate files* (this attempts to reconstruct the application's original source files if corresponding debug information is available)

   **NOTE:** if you are new to assembler/assembly language, check out this [x86 Assembly Guide](https://www.cs.virginia.edu/~evans/cs216/guides/x86.html)

8. Refine the output by analyzing the disassembly, updating the object hints and re-running *wcdatool* (i.e. loop steps 5-8):
   - Identify and add hints for regions in code objects that are actually data (look for `; misplaced item` comments, `(bad)` assembly instructions and labels with `; access size` comments)
   - Identify and add hints for regions in data objects that are actually code (look for `call`/`jmp` instructions in code objects with fixup targets pointing to data objects)
   - Check section `Possible object hints` of *wcdatool*'s output/log for suggestions (not guaranteed to be correct, but likely a good starting point)
   - *The ultimate goal here is to eliminate all (or at least most) warnings issued by wcdatool*. Each warning points out a region of the disassembly that does currently seem flawed and therefore requires further attention/investigation. Note that there is a *cascading effect* at work (e.g. a region of data that is falsely intepreted as code may produce bogus branches, leading to further issues), thus warnings should be tackled one (or few) at a time from first to last with *wcdatool* re-runs in between

   **NOTE:** this is by far the most time-consuming part, but *crucial* to achieve good and clean results (!)

## How to contact me

If you want to get in touch with me, give feedback, ask questions or simply need someone to talk to, please open an [Issue](https://github.com/fonic/wcdatool/issues) here on GitHub. Make sure to leave an email address if you prefer personal/private contact.
