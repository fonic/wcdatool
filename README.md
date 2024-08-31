# Watcom Disassembly Tool (wcdatool)

Tool to aid disassembling DOS applications created with the *Watcom* toolchain.

## Donations

I'm striving to become a full-time developer of [Free and open-source software (FOSS)](https://en.wikipedia.org/wiki/Free_and_open-source_software). Donations help me achieve that goal and are highly appreciated.

<a href="https://www.buymeacoffee.com/fonic"><img src="https://raw.githubusercontent.com/fonic/donate-buttons/main/buymeacoffee-button.png" alt="Buy Me A Coffee" height="35"></a>&nbsp;&nbsp;&nbsp;<a href="https://paypal.me/fonicmaxxim"><img src="https://raw.githubusercontent.com/fonic/donate-buttons/main/paypal-button.png" alt="Donate via PayPal" height="35"></a>&nbsp;&nbsp;&nbsp;<a href="https://ko-fi.com/fonic"><img src="https://raw.githubusercontent.com/fonic/donate-buttons/main/kofi-button.png" alt="Donate via Ko-fi" height="35"></a>

## Watcom Toolchain

Many DOS applications of the 90s, especially games, were developed using the *Watcom* toolchain. Examples are *DOOM*, *Warcraft*, *Syndicate*, *Mortal Kombat*, just to name a few.

Most end-users probably never have heard of *Watcom*, but might remember applications displaying a startup banner reading something like this: `DOS/4G(W) Protected Mode Run-time [...]`. *DOS/4G(W)* was a popular DOS extender bundled with the *Watcom* toolchain, allowing DOS applications to run in *32-bit protected mode*.

Nowadays, the *Watcom* toolchain is open source and lives on as [Open Watcom](http://openwatcom.org/) / [Open Watcom v2 Fork](https://open-watcom.github.io/).

## Why create another disassembly tool?

The idea for this tool emerged when I discovered that one of my all-time favorite games, *Mortal Kombat*, was mainly written in Assembler (more or less directly ported from the arcade version) and was released *unstripped* (i.e. executable contains debug symbols). I tried using various decompilation/disassembly tools on it, only to discover that none seemed to be capable of dealing with the specifics of *Watcom*-based applications.

Thus, I began writing my own tool. What originally started out as *mkdecomptool* specifically for *Mortal Kombat* is now the general-purpose *Watcom Disassembly Tool (wcdatool)*.

Note that while wcdatool performs the tasks it is designed for quite well, it is not intended to compete with or replace high-end tools like *IDA Pro* or *Ghidra*.

## Current state / future development

Wcdatool works quite well in its current state - you'll get a well-readable, reasonably structured disassembly output (*objdump* format, *Intel* syntax). Check out issues [#9](https://github.com/fonic/wcdatool/issues/9) and [#11](https://github.com/fonic/wcdatool/issues/11) for games other than *Mortal Kombat* that wcdatool worked nicely for thus far. **Please note that wcdatool works best when used on executables that contain debug symbols.** If you come across other *unstripped* *Watcom*-based DOS applications that may be used for further testing and development, please let me know.

**However, the current approach has reached its EOL.** There is no point in advancing it any further (aside from fixing bugs), as there are limits inherent to the fundamental design that cannot be overcome easily. Thus, the next major goal is to cleanly *rewrite the disassembler module* and transition from *static code disassembly* to *execution flow tracing* (e.g. *Mortal Kombat 2* executable contains code within its data object, which is neither discovered nor analyzed with the current approach). Also, instead of treating objects separately, a *linear unified address space* containing all object data shall be implemented. This will allow to *apply fixups on a binary level*, which should simplify dealing with references that cross object boundaries and with placeholders (stubs) that are replaced via fixups at run time.

Last but not least, wcdatool in its current state is relatively slow, as performance has not been the main focus during development. [Cython](https://cython.org/) might be utilized in the future to increase performance.

## Output sample

Output sample for *Fatal Racing* (`FATAL.EXE`) - the left side shows the reconstructed source files, the right side shows a portion of formatted disassembly:

![Screenshot](https://raw.githubusercontent.com/fonic/wcdatool/master/SCREENSHOT.png)

## How to use it

There are multiple ways to use *wcdatool*, but the following instructions should get you started. Don't let the amount of information provided below discourage you, the tool is easier to use than it might seem. The instructions assume that you are using *Linux*. For *Windows* users, the easiest way to go is to use *Windows Subsystem for Linux (WSL)*:

1. Requirements:

   Wcdatool: *Python (>=3.6.0)*, *wdump* (part of [Open Watcom v2](https://open-watcom.github.io/)), *objdump* (part of [binutils](https://sourceware.org/binutils/))<br/>
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

   Object hints may be used to manually affect the disassembly process (e.g. force decoding of certain regions as code/data, specify data decoding mode, define data structs, add comments). Please refer to included object hint files for *Mortal Kombat*, *Fatal Racing* and *Pac-Man VR* for details regarding capabilities and syntax.

   **NOTE:** hint files must be stored as `wcdatool/Hints/<name-of-executable>.txt` (case-sensitive, e.g. `wcdatool/Executables/MK1.EXE` -> `wcdatool/Hints/MK1.EXE.txt`) to be picked up automatically by the included scripts

6. Let *wcdatool* process all provided executables (for the example executables listed in step 4, this will take ~3min. and generate ~1.5GB worth of data):
   ```
   # wcdatool/Scripts/process-all-executables.sh
   ```

   -or- Let *wcdatool* process a single executable:
   ```
   # wcdatool/Scripts/process-single.executable.sh <name-of-executable>
   ```

   -or- Run *wcdatool* manually (use `--help` to display detailed usage information or [see below](#wcdatool-usage-information)):
   ```
   # python wcdatool/Wcdatool/wcdatool.py -od wcdatool/Output -wao wcdatool/Hints/<name-of-executable>.txt wcdatool/Executables/<name-of-executable>
   ```

   **NOTE:** it is completely normal and expected for *wcdatool* to produce LOTS of warnings; ignore those when just getting started (see step 8 for details)

7. Have a look at the results in `wcdatool/Output`:
   - File `<name-of-executable>_zzz_log.txt` contains *log messages* (same as console output, but without coloring/formatting)
   - Files `<name-of-executable>_disasm_object_x_disassembly_plain.asm` contain *plain disassembly* (unmodified *objdump* output, useful for reference)
   - Files `<name-of-executable>_disasm_object_x_disassembly_formatted.asm` contain *formatted disassembly* (this is arguably the most interesting/useful output)
   - Files `<name-of-executable>_disasm_object_x_disassembly_formatted_deduplicated.asm` contain *formatted deduplicated disassembly* (same as above, but with data portions being compressed for increased readability where applicable)
   - Folder `<name-of-executable>_modules` contains *formatted disassembly split into separate files* (same as above, additionally attempts to reconstruct an application's original source files if corresponding debug information is available)

   **NOTE:** if you are new to assembler/assembly language, check out this [x86 Assembly Guide](https://www.cs.virginia.edu/~evans/cs216/guides/x86.html)

8. Refine the output by analyzing the disassembly, updating the object hints and re-running *wcdatool* (i.e. loop steps 5-8):
   - Identify and add hints for regions in code objects that are actually data (look for `; misplaced item` comments, `(bad)` assembly instructions and labels with trailing `; access size` comments)
   - Identify and add hints for regions in data objects that are actually code (look for `call`/`jmp` instructions in code objects with fixup targets pointing to data objects)
   - Check section `Possible object hints` of *wcdatool*'s console output / log file for suggestions (not guaranteed to be correct, but likely a good starting point)
   - *The ultimate goal is to eliminate all (or at least most) warnings issued by wcdatool*. Each warning points out a region of the disassembly that does currently seem flawed and therefore requires further attention/investigation. Note that there is a *cascading effect* at work (e.g. a region of data that is falsely intepreted as code may produce bogus branches, leading to further warnings), thus warnings should be tackled one (or few) at a time from first to last with *wcdatool* re-runs in between

   **NOTE:** this is by far the most time-consuming part, but *crucial* to achieve good and clean results (!)

## Wcdatool usage information

```
Usage: wcdatool.py [-wde|--wdump-exec PATH] [-ode|--objdump-exec PATH]
                   [-wdo|--wdump-output PATH] [-wao|--wdump-addout PATH]
                   [-od|--output-dir PATH] [-cm|--color-mode VALUE]
                   [-id|--interactive-debugger] [-is|--interactive-shell]
                   [-h|--help] FILE

Tool to aid disassembling DOS applications created with the Watcom toolchain.

Positionals:
  FILE                            Path to input executable to disassemble
                                  (.exe file)

Options:
  -wde PATH, --wdump-exec PATH    Path to wdump executable (default: 'wdump')
  -ode PATH, --objdump-exec PATH  Path to objdump executable (default:
                                  'objdump')
  -wdo PATH, --wdump-output PATH  Path to file containing pre-generated wdump
                                  output to read/parse instead of running
                                  wdump
  -wao PATH, --wdump-addout PATH  Path to file containing additional wdump
                                  output to read/parse (mainly used for object
                                  hints)
  -od PATH, --output-dir PATH     Path to output directory for storing
                                  generated content (default: '.')
  -cm VALUE, --color-mode VALUE   Enable color mode (choices: 'auto', 'true',
                                  'false') (default: 'auto')
  -id, --interactive-debugger     Drop to interactive debugger before exiting
                                  to allow inspecting internal data structures
  -is, --interactive-shell        Drop to interactive shell before exiting to
                                  allow inspecting internal data structures
  -h, --help                      Display usage information (this message)
```

## How to contact me

If you want to get in touch with me, give feedback, ask questions or simply need someone to talk to, please open an [Issue](https://github.com/fonic/wcdatool/issues) here on GitHub. Make sure to leave an email address if you prefer personal/private contact.

##

_Last updated: 08/31/24_
