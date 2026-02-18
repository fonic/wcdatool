# Watcom Disassembly Tool (wcdatool)

Tool to aid disassembling DOS applications created with the *Watcom Toolchain*.

## Donations

I'm a strong supporter of [Free and open-source software (FOSS)](https://en.wikipedia.org/wiki/Free_and_open-source_software). Donations help keeping my projects alive and are highly appreciated.

<a href="https://www.buymeacoffee.com/fonic"><img src="https://raw.githubusercontent.com/fonic/donate-buttons/main/buymeacoffee-button.png" alt="Buy Me A Coffee" height="35"></a>&nbsp;&nbsp;&nbsp;<a href="https://paypal.me/fonicmaxxim"><img src="https://raw.githubusercontent.com/fonic/donate-buttons/main/paypal-button.png" alt="Donate via PayPal" height="35"></a>&nbsp;&nbsp;&nbsp;<a href="https://ko-fi.com/fonic"><img src="https://raw.githubusercontent.com/fonic/donate-buttons/main/kofi-button.png" alt="Donate via Ko-fi" height="35"></a>

## Table Of Contents

- [The Watcom Toolchain](#the-watcom-toolchain)
- [Yet Another Disassembly Tool?](#yet-another-disassembly-tool)
- [Current State / Future Development](#current-state--future-development)
- [Output Sample](#output-sample)
- [**Getting Started**](#getting-started)
- [Wcdatool Usage Information](#wcdatool-usage-information)
- [Contact Information](#contact-information)

## The Watcom Toolchain

Many DOS applications of the 90s, especially games, were developed using the *Watcom Toolchain*. Notable examples are *DOOM*, *Warcraft*, *Syndicate* and *Mortal Kombat*, just to name a few.

Most end-users probably never have heard of *Watcom*, but might remember applications displaying a startup banner reading something like this: `DOS/4G(W) Protected Mode Run-time [...]`. *DOS/4G(W)* was a popular DOS extender bundled with the *Watcom Toolchain*, allowing DOS applications to run in *32-bit protected mode* and thus being able to reach well beyond the limits of 16-bit (MS-)DOS.

Nowadays, the *Watcom Toolchain* is open source and lives on as [Open Watcom](http://openwatcom.org/) / [Open Watcom v2 Fork](https://open-watcom.github.io/).

## Yet Another Disassembly Tool?

The idea for this tool emerged when I discovered that one of my all-time favorite games, *Mortal Kombat* (CD version), was mainly written in Assembler (almost a line-by-line port of the arcade version) and was released *unstripped* (i.e. executable contains debug symbols). I tried using various decompilation/disassembly tools on it, only to realize that none seemed to be capable of dealing with the specifics of *Watcom*-based applications.

Hence, I began writing my own tool. What initially started out as *mkdecomptool* specifically for *Mortal Kombat* gradually became the now general-purpose *Watcom Disassembly Tool (wcdatool)*.

Note that while wcdatool performs the tasks it is designed for quite well, it is not intended to compete with or replace high-end tools like *IDA Pro* or *Ghidra*.

## Current State / Future Development

Wcdatool works quite well in its current state - you'll get a well-readable, reasonably structured disassembly output (*objdump* format, *Intel* syntax). Check out issues [#9](https://github.com/fonic/wcdatool/issues/9) and [#11](https://github.com/fonic/wcdatool/issues/11) for games other than *Mortal Kombat* that wcdatool worked nicely for thus far. **Please note that wcdatool works best when used on executables that contain debug symbols.** If you come across other *unstripped* *Watcom*-based DOS applications that may be used for further testing and development, [please let me know](https://github.com/fonic/wcdatool/issues/new/choose).

The next major goal is to cleanly *rewrite the disassembler module* and transition from *static code disassembly* to *execution flow tracing*. Also, instead of treating an executable's objects separately, a *linear unified address space* containing all object data will be the basis for future processing. This will allow to *apply fixups on a binary level*, which should simplify dealing with references that cross object boundaries, such as placeholders/stubs (which are patched via fixups at run time). *Mortal Kombat 2's executable* will be baseline for the new approach, as it contains code regions within its data object (which are currently neither discovered nor processed) and extensively uses placeholders/stubs for jump/call targets that cross object boundaries (which are currently not handled properly).

Last but not least, wcdatool in its current state is relatively slow, as performance has not been the main focus during development. [Cython](https://cython.org/) might be utilized in the future to increase performance.

## Output Sample

Output sample for *Fatal Racing* (`FATAL.EXE`) - the left side shows the reconstructed source files, the right side shows a portion of formatted disassembly:

![Screenshot](https://raw.githubusercontent.com/fonic/wcdatool/master/SCREENSHOT.png)

## Getting Started

There are multiple ways to use *wcdatool*, but the following instructions should get you started. Don't let the amount of information provided below discourage you, the tool is easier to use than it might seem. The instructions assume that you are using *Linux*. For *Windows* users, the easiest way to go is to use [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/install):

1. **Check the following requirements:**

   **Wcdatool:**<br/>
   *Python (>=3.6.0)*, *wdump* (part of [Open Watcom v2](https://open-watcom.github.io/)), *objdump* (part of [binutils](https://sourceware.org/binutils/))<br/>
   (both *wdump* and *objdump* need to be accessible via `PATH`)

   **Open Watcom v2:**<br/>
   *gcc* -or- *clang* (for 64-bit builds), *DOSEMU* -or- *DOSBox* (for *wgml* utility)<br/>
   (only relevant if *Open Watcom v2* is built from sources; the project also provides [pre-compiled binaries](https://github.com/open-watcom/open-watcom-v2/releases))

2. **Clone *wcdatool*'s repository** (-or- download and extract a [release](https://github.com/fonic/wcdatool/releases)):
   ```
   # git clone https://github.com/fonic/wcdatool.git
   ```

3. **Download, build and install *Open Watcom v2*** (-or- download and install [pre-compiled binaries](https://github.com/open-watcom/open-watcom-v2/releases)):
   ```
   # cd wcdatool/OpenWatcom
   # ./1_download.sh
   # ./2_build.sh
   # ./3_install_linux.sh /opt/openwatcom /opt/bin/openwatcom
   ```
   **NOTE:** these scripts are provided for convenience, they are not part of the *Open Watcom v2* project itself

4. **Copy the executables to be disassembled to `wcdatool/Executables`**, e.g. for *Mortal Kombat*:
   ```
   # cp <source-dir>/MK1.EXE wcdatool/Executables
   # cp <source-dir>/MK2.EXE wcdatool/Executables
   # cp <source-dir>/MK3.EXE wcdatool/Executables
   ```
   **NOTE:** file names of executables are used to locate corresponding object hint files (see step 5)

5. **Create/update object hint files in `wcdatool/Hints`** *(optional; skip when just getting started)*:

   Object hints may be used to manually affect the disassembly process (e.g. force decoding of certain regions as code/data, specify data decoding mode, define data structs, add comments). Please refer to included object hint files for *Mortal Kombat*, *Fatal Racing* and *Pac-Man VR* for details regarding capabilities and syntax.

   **NOTE:** hint files must be stored as `wcdatool/Hints/<name-of-executable>.txt` (case-sensitive, e.g. `wcdatool/Executables/MK1.EXE` -> `wcdatool/Hints/MK1.EXE.txt`) to be picked up automatically by the included scripts

6. **Let *wcdatool* process all provided executables** (for the example executables listed in step 4, this will take ~3min. and generate ~1.5GB worth of data):
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

7. **Have a look at the results in `wcdatool/Output`**:
   - File `<name-of-executable>_zzz_log.txt` contains *log messages* (same as console output, but without coloring/formatting)
   - Files `<name-of-executable>_disasm_object_x_disassembly_plain.asm` contain *plain disassembly* (unmodified *objdump* output, useful for reference)
   - Files `<name-of-executable>_disasm_object_x_disassembly_formatted.asm` contain *formatted disassembly* (this is arguably the most interesting/useful output)
   - Files `<name-of-executable>_disasm_object_x_disassembly_formatted_deduplicated.asm` contain *formatted deduplicated disassembly* (same as above, but with data portions being compressed for increased readability where applicable)
   - Folder `<name-of-executable>_modules` contains *formatted disassembly split into separate files* (same as above, attempts to reconstruct an application's original source file structure if corresponding debug information is available)

   **NOTE:** if you are new to assembler/assembly language, check out this [x86 Assembly Guide](https://www.cs.virginia.edu/~evans/cs216/guides/x86.html)

8. **Refine the output by analyzing the disassembly**, updating the object hints and re-running *wcdatool* (i.e. loop steps 5-8):
   - Identify and add hints for regions in code objects that are actually data (look for `; misplaced item` comments, `(bad)` assembly instructions and labels with trailing `; access size` comments)
   - Identify and add hints for regions in data objects that are actually code (look for `call`/`jmp` instructions in code objects with fixup targets pointing to data objects)
   - Check section `Possible object hints` of *wcdatool*'s console output / log file for suggestions (not guaranteed to be correct, but likely a good starting point)
   - *The ultimate goal is to eliminate all (or at least most) warnings issued by wcdatool*. Each warning points out a region of the disassembly that does currently seem flawed and therefore requires further attention/investigation. Note that there is a *cascading effect* at work (e.g. a region of data that is falsely intepreted as code may produce bogus branches, leading to further warnings), thus warnings should be tackled one (or few) at a time from first to last with *wcdatool* re-runs in between

   **NOTE:** this is by far the most time-consuming part, but *crucial* to achieve good and clean results (!)

## Wcdatool Usage Information

```
Usage: wcdatool.py [-wde|--wdump-exec PATH] [-ode|--objdump-exec PATH]
                   [-wdo|--wdump-output PATH] [-wao|--wdump-addout PATH]
                   [-od|--output-dir PATH] [-cm|--color-mode VALUE]
                   [-id|--interactive-debugger] [-is|--interactive-shell]
                   [-h|--help] FILE

Tool to aid disassembling DOS applications created with the Watcom Toolchain.

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

## Contact Information

If you want to get in touch with me, give feedback, ask questions or simply need someone to talk to, please [open an issue](https://github.com/fonic/wcdatool/issues/new/choose) here on GitHub. Make sure to provide an email address if you prefer personal/private contact.

##

_Last updated: 10/24/24_
