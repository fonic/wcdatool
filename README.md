# Watcom Decompilation Tool (wcdctool)

Tool to aid decompiling DOS applications created with the Watcom toolchain.

## Watcom Toolchain

Many DOS applications of the 90s, especially games, were developed using the *Watcom* toolchain. Examples are *DOOM*, *Warcraft*, *Syndicate*, *Mortal Kombat*, just to name a few. Most end-users probably never have heard of *Watcom*, but might remember applications displaying a startup banner reading something like `DOS/4G(W) Protected Mode Run-time [...]`. *DOS/4G(W)* was a popular DOS extender bundled with the Watcom toolchain.

Nowadays, the *Watcom* toolchain is open source and lives on as [Open Watcom](http://openwatcom.org/) / [Open Watcom v2 Fork](https://open-watcom.github.io/).

## Why create another decompilation tool?

The idea for this tool emerged when I discovered that one of my all-time favorite games, *Mortal Kombat*, was mainly written in Assembler (more or less directly ported from the arcade version) and, on top of that, released unstripped (i.e. with debug symbols kept intact)<sup>(*)</sup>. The latter was most likely unintentional and/or happened by accident, but that's just a guess. I tried using various decompilation tools on it, only to discover that none seems to be capable of dealing with the specifics of Watcom-based applications.

Thus, I began writing my own tool. What started out as *mkdecomptool* specifically for Mortal Kombat is now the general-purpose *Watcom Decompilation Tool (wcdctool)*.

<sup>(*)</sup> *Applies to Mortal Kombat 1 CD Version (MK1.EXE 1.157.222 bytes), Mortal Kombat 2 CD Version (MK2.EXE 1.315.079 bytes) and Mortal Kombat Trilogy (MKTRIL.EXE 3.059.926 bytes). AFAICT does not apply to Mortal Kombat 3.*

## Development and current state

Wcdctool is work in progress. You can tell from looking at the source code - there's tons of TODO, TESTING, tbd etc. flying around. Nevertheless, it works quite well in its current state - you'll get a well-readable, reasonably structured disassembly output. Please note that the tool was mainly tested on *Mortal Kombat*, therefore results for other applications may vary greatly. If you come across other unstripped Watcom-based DOS applications, please let me know!

Open major TODOs:
- Extend code segment/data segment reference analysis by making use of relocation data (moderately complex)
- Split disassembly into orginal source files (relatively easy)
- Make disassembly (re-)compilable (complex, I currently lack the required skills/experience to accomplish this)

Sadly, I currently have limited resources to continue working on this project. Thus, don't expect any quantum leaps in short periods of time.

If you're interested in joining the effort (especially regarding decompiling *Mortal Kombat*), please get in touch with me.

## How to use it

There are multiple ways to use *wcdctool*, but this should get you started:

1. Requirements:

   Open Watcom: *gcc* -or- *clang* (for 64-bit build), *DOSEMU* -or- *DOSBox* (for wgml utility)<br/>
   wcdctool: *Python >= 3.6.0*, *wdump* (part of Open Watcom), *objdump*

2. Download wcdctool:
   ```
   # git clone https://github.com/fonic/wcdctool.git
   ```

3. Download, build and install Open Watcom:
   ```
   # cd wcdctool/OpenWatcom
   # ./0_download.sh
   # ./1_build.sh
   # ./2_install_linux.sh /opt/openwatcom /opt/bin/openwatcom
   ```
   **NOTE:** I created those scripts myself for convenience, they are not part of *Open Watcom*

4. Copy application executables (.exe/.EXE) to `wcdctool/Executables`, e.g. for *Mortal Kombat*:
   ```
   # cp <source-dir>/MK1.EXE wcdctool/Executables
   # cp <source-dir>/MK2.EXE wcdctool/Executables
   # cp <source-dir>/MK3.EXE wcdctool/Executables
   # cp <source-dir>/MKTRIL.EXE wcdctool/Executables
   ```
   **NOTE:** make sure to correctly name executables so *wcdctool* finds additional wdump output files (`_wao.txt`)

5. Let wcdctool process all provided executables:
   ```
   # source /opt/bin/openwatcom
   # cd wcdctool/Executables
   # ./x_process_all.sh
   ```
   **NOTE:** for the executables listed in 4., this will take ~ 5-10 min. and generate ~ 1 GB worth of data

6. Have a look at the results in `wcdctool/Output`

## Fun facs about Mortal Kombat 1 CD Version

Here are some interesting details I gathered from analyzing Mortal Kombat 1 CD Version's disassembly:
- Disassembly is about 70.250 lines (only code, i.e. plain without any formatting)
- About 40.550 lines form the actual game code, the rest is sound library (AIL) and standard library (strlen, printf, ...)
- For sound, the *Audio Interface Library (AIL) v3.02* is used (predecessor of *Miles Sound System*)
- Everything AI-related is called *drone* in game code (e.g. routines *DRONE_DUCK*, *DRONE_FLY_KICK*)
- Some familiar names/terms do not show up in the game code at all, e.g.:<br/>
  *Sonya [Blade]* -> called *liz* in game code (probably short for *Elizabeth Malecki*, the actress portraying the character)<br/>
  *Johnny [Cage]* -> called *vd* in game code (probably meaning/referring to *Van Damme*)<br/>
  *Shang Tsung* -> called *emperor* in game code<br/>
  *Reptile* -> called *gninja* in game code (probably meaning *Green Ninja*)<br/>
- As was known before, Reptile is only a special flag, not a real character (variable *F_GNINJA*)
- Goro, Shang Tsung and Reptile are only implemented/handled in *drone* code (i.e. in AI routines). That's why all attempts of making them playable by simply forcing the player's character to a certain value failed in the past. There's simply no code in the player routines to handle them
- There are general purpose variables *A2-A14* + *B0-B15* that are being used throughout the game code. The original arcade machine was based on a CPU with 2 register files, each with 15 registers. So, it would seem they simply replaced registers with RAM-based variables to facilitate the porting process
- The game was compiled from the following source files:<br/>
  *C:\KOMBAT1\kombat.cpp, BAKGND.ASM, BGND.ASM, CMOS.ASM, DIAGTEXT.ASM, DMA.ASM, DMA_CMP.ASM, drone.ASM, JOY.ASM, MAIN.ASM, MKAMODE.ASM, MKBLOOD.ASM, MKCANNED.ASM, MKCHOP.ASM, MKDISP.ASM, MKEMP.ASM, MKEND.ASM, MKFX.ASM, MKGORO.ASM, MKHSTD.ASM, MKINIT.ASM, MKINTRO.ASM, MKSEL.ASM, MKSETUP.ASM, MKSOUND.ASM, MKTEXT.ASM, MKUTIL.ASM, MOVES.ASM, MPROC.ASM, PALL.ASM, REACT.ASM, RLL_FCNZ.ASM, RLL_FSHA.ASM, RLL_FWNZ.ASM, RLL_SHAD.ASM, RLL_WNZ.ASM, RLL_WCNZ.ASM, SPECIAL.ASM, SPECIAL2.ASM, UTIL.ASM, EMP.ASM, RAIDEN.ASM, sfx.ASM, R:\NET\LIBS\AIL\DEV3\FLAT\aildebug.c, R:\NET\LIBS\AIL\DEV3\FLAT\dllload.c, R:\NET\LIBS\AIL\DEV3\FLAT\ail.c, R:\NET\LIBS\AIL\DEV3\FLAT\ailss.c, R:\NET\LIBS\AIL\DEV3\FLAT\ailsfile.c, R:\NET\LIBS\AIL\DEV3\FLAT\ailxmidi.c, R:\NET\LIBS\AIL\DEV3\FLAT\ailxdig.c*

## How to contact me

If you want to get in touch with me, give feedback, ask questions or simply need someone to talk to, please open an [Issue](https://github.com/fonic/wcdctool/issues) here on GitHub.
