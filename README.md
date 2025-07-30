<!-- ![Tests](https://img.shields.io/github/workflow/status/michelcrypt4d4mus/pdfalyzer/tests?label=tests)  -->
![Python Version](https://img.shields.io/pypi/pyversions/pdfalyzer)
[![GithubRelease](https://img.shields.io/github/v/release/michelcrypt4d4mus/pdfalyzer?sort=semver)](https://pypi.org/project/pdfalyzer/)
[![GitHub last commit](https://img.shields.io/github/last-commit/michelcrypt4d4mus/pdfalyzer)](https://github.com/michelcrypt4d4mus/pdfalyzer)
![PyPiRelease](https://img.shields.io/pypi/v/pdfalyzer)
![Downloads](https://img.shields.io/pypi/dm/pdfalyzer)


# THE PDFALYZER

![](https://github.com/michelcrypt4d4mus/pdfalyzer/raw/master/doc/svgs/rendered_images/basic_tree.png)

A PDF analysis tool for [visualizing](#example-output) the inner tree-like data structure[^1] of a PDF in [spectacularly large and colorful diagrams](#example-output) as well as scanning the binary streams embedded in the PDF for hidden potentially malicious content. The Pdfalyzer makes heavy use of YARA (via [The Yaralyzer](https://github.com/michelcrypt4d4mus/yaralyzer)) for matching/extracting byte patterns.

**PyPi Users:** This document renders a lot better [on GitHub](https://github.com/michelcrypt4d4mus/pdfalyzer). Pictures, footnotes, etc.

### Quick Start
```sh
pipx install pdfalyzer
pdfalyze "martin_heidegger-being_illmatic.pdf"
```

### What It Do
1. **Generate in depth visualizations of PDF tree structures**[^1]. Shows every property of every PDF object at a glance. See the [Example Output](#example-output) section below for details.
1. **Scan for mad sus content with a bunch of PDF specific [YARA](https://github.com/VirusTotal/yara-python) rules.**
1. **Forcibly decode suspect bytes**. [The Yaralyzer](https://github.com/michelcrypt4d4mus/yaralyzer) does the heavy lifting.
1. **Display detailed information about embedded fonts.** With character maps.
1. **Usable as a library for your own PDF related code.**

If you're looking for one of these things this may be the tool for you.


### What It Don't Do
This tool is mostly for examining/working with a PDF's data and logical structure. As such it doesn't have much to offer as far as extracting text, rendering[^3], writing, etc. etc.

-------------

# Installation

Installation with [pipx](https://pypa.github.io/pipx/)[^4] is preferred though `pip3` / `pip` should also work.
```sh
pipx install pdfalyzer
```

See [PyPDF installation notes](https://github.com/py-pdf/pypdf#installation) about `PyCryptodome` if you plan to `pdfalyze` any files that use AES encryption.

If you are on macOS someone out there was kind enough to make [The Pdfalyzer available via homebrew](https://formulae.brew.sh/formula/pdfalyzer) so `brew install pdfalyzer` should work.

### Troubleshooting
1. If you used `pip3` instead of `pipx` and have an issue you should try to install with `pipx`.
1. If you run into an issue about missing YARA try to install [yara-python](https://pypi.org/project/yara-python/).
1. If you encounter an error building the python `cryptography` package check your `pip` version (`pip --version`). If it's less than 22.0, upgrade `pip` with `pip install --upgrade pip`.
1. If you get a YARA internal error number you can look up what it actually means [here](https://github.com/VirusTotal/yara/blob/master/libyara/include/yara/error.h).
1. If you can't get the `pdfalyze` command to work try `python -m pdfalyzer`. It's an equivalent but more portable version of the same command that does not rely on your python script paths being set up in a sane way.
1. While The Pdfalyzer has been tested on quite a few large and very complicated PDFs there are no doubt a bunch of edge cases that will trip up the code. Sifting through the various interconnected internal PDF objects and building the correct tree representation is much, much harder than it should be and requires multiple scans and a little bit of educated guessing. If a PDF fails to parse and you hit an error please open [a GitHub issue](https://github.com/michelcrypt4d4mus/pdfalyzer/issues) with the compressed (`.zip`, `.gz`, whatever) PDF that is causing the problem attached (if possible) and I'll take a look when I can. I will _not_ take a look at any uncompressed PDFs due to the security risks so make sure you zip it before you ship it.
1. On Linux if you encounter an error building `wheel` or `cffi` you may need to install some packages:
   ```bash
   sudo apt-get install build-essential libssl-dev libffi-dev rustc
   ```

-------------

# Usage

Run `pdfalyze --help` to see usage instructions. As of right now these are the options:

![](https://github.com/michelcrypt4d4mus/pdfalyzer/raw/master/doc/svgs/rendered_images/pdfalyze_help.png)

## Runtime Options
If you provide none of the flags in the `ANALYSIS SELECTION` section of the `--help` then all of the analyses will be done _except_ the `--streams`.  In other words, these two commands are equivalent:

1. `pdfalyze lacan_buys_the_dip.pdf`
1. `pdfalyze lacan_buys_the_dip.pdf -d -t -r -f -y -c`

The `--streams` output is the one used to hunt for patterns in the embedded bytes and can be _extremely_ verbose depending on the `--quote-char` options chosen (or not chosen) and contents of the PDF. [The Yaralyzer](https://github.com/michelcrypt4d4mus/yaralyzer) handles this task; if you want to hunt for patterns in the bytes other than bytes surrounded by backticks/frontslashes/brackets/quotes/etc. you may want to use The Yaralyzer directly. As The Yaralyzer is a prequisite for The Pdfalyzer you may already have the `yaralyze` command installed and available.

### Setting Command Line Options Permanently With A `.pdfalyzer` File
When you run `pdfalyze` on some PDF the tool will check for a file called `.pdfalyzer` first in the current directory and then in the home directory. If it finds a file in either such place it will load configuration options from it. Documentation on the options that can be configured with these files lives in [`.pdfalyzer.example`](.pdfalyzer.example) which doubles as an example file you can copy into place and edit to your needs. Handy if you find yourself typing the same command line options over and over again.

### Environment Variables
Even if you don't configure your own `.pdfalyzer` file you may still glean some insight from reading the descriptions of the various variables in [`.pdfalyzer.example`](.pdfalyzer.example); there's a little more exposition there than in the output of `pdfalyze -h`.

### Colors And Themes
Run `pdfalyzer_show_color_theme` to see the color theme employed.

### Guarantees
Warnings will be printed if any PDF object ID between 1 and the `/Size` reported by the PDF itself could not be successfully placed in the tree. If you do not get any warnings then all[^2] of the inner PDF objects should be seen in the output.

## Example Usage
[BUFFERZONE Team](https://bufferzonesecurity.com) posted [an excellent example](https://bufferzonesecurity.com/the-beginners-guide-to-adobe-pdf-malware-reverse-engineering-part-1/) of how one might use The Pdfalyzer in tandem with [Didier Stevens' PDF tools](#installing-didier-stevenss-pdf-analysis-tools) to investigate a potentially malicious PDF (archived in [the `doc/` dir in this repo](./doc/) if the link rots).

-------------

## Use As A Code Library
For info about setting up a dev environment see [Contributing](#contributing) below.

At its core The Pdfalyzer is taking PDF internal objects gathered by [PyPDF](https://github.com/py-pdf/pypdf) and wrapping them in [AnyTree](https://github.com/c0fec0de/anytree)'s `NodeMixin` class.  Given that things like searching the tree or accessing internal PDF properties will be done through those packages' code it may be helpful to review their documentation.

As far as The Pdfalyzer's unique functionality goes, [`Pdfalyzer`](pdfalyzer/pdfalyzer.py) is the class at the heart of the operation. It holds the PDF's logical tree as well as a few other data structures. Chief among these are the [`FontInfo`](pdfalyzer/font_info.py) class which pulls together various properties of a font strewn across 3 or 4 different PDF objects and the [`BinaryScanner`](pdfalyzer/binary/binary_scanner.py) class which lets you dig through the embedded streams' bytes looking for suspicious patterns.

Here's a short intro to how to access these objects:

```python
from pdfalyzer.pdfalyzer import Pdfalyzer

# Load a PDF and parse its nodes into the tree.
pdfalyzer = Pdfalyzer("/path/to/the/evil_or_non_evil.pdf")
actual_pdf_tree: PdfTreeNode = pdfalyzer.pdf_tree

# The PdfalyzerPresenter handles formatting/prettifying output
from pdfalyzer.output.pdfalyzer_presenter import PdfalyzerPresenter
PdfalyzerPresenter(pdfalyzer).print_everything()

# Iterate over all nodes in the PDF tree
for node in pdfalyzer.node_iterator():
    do_stuff(node)

# Iterate over the fonts
for font in pdfalyzer.font_infos:
    do_stuff(font)

# Iterate over all stream objects:
for node in pdfalyzer.stream_nodes():
    do_stuff(node.stream_data)

# Find an internal PDF object by its ID in the PDF
node = pdfalyzer.find_node_by_idnum(44)
pdf_object: PdfObject = node.obj

# Use anytree's findall_by_attr() to find nodes with a given property
from anytree.search import findall_by_attr
page_nodes = findall_by_attr(pdfalyzer.pdf_tree, name='type', value='/Page')

# Iterate over backtick quoted strings from a font binary and process them
font_info: FontInfo = pdfalyzer.font_infos[0]

for backtick_quoted_string in font.binary_scanner.extract_backtick_quoted_bytes():
    do_stuff(backtick_quoted_string)
```

-------------

# Example Output
The Pdfalyzer can export visualizations to HTML, ANSI colored text, and SVG images using the file export functionality that comes with [Rich](https://github.com/Textualize/rich). SVGs can be turned into `png` format images with a tool like Inkscape or `cairosvg` (Inkscape works a lot better in our experience). See `pdfalyze --help` for the specifics.


## Basic Tree View
As you can see the suspicious `/OpenAction` relationship is highlighted bright red, as would be a couple of other sus PDF instructions like `/JavaScript` or `/AcroForm` if they exist in the PDF being pdfalyzed.

The dimmer (as in "harder to see") nodes[^5] marked with `Non Child Reference` give you a way to visualize the relationships between PDF objects that exist outside of the tree structure's parent/child relationships.

![](https://github.com/michelcrypt4d4mus/pdfalyzer/raw/master/doc/svgs/rendered_images/basic_tree.png)

That's a pretty basic document. [Here's the basic tree for a more complicated PDF containing an NMAP cheat sheet](doc/svgs/rendered_images/NMAP_Commands_Cheat_Sheet_and_Tutorial.pdf.tree.svg.png).

## Rich Tree View
This image shows a more in-depth view of of the PDF tree for the same document shown above. This tree (AKA the "rich" tree) has almost everything. Shows all PDF object properties, all relationships between objects, and sizable previews of any binary data streams embedded or encrypted in the document. Note that in addition to `/OpenAction`, the Adobe Type1 font binary is also red (Google's project zero regards any Adobe Type1 font as "mad sus").

![](https://github.com/michelcrypt4d4mus/pdfalyzer/raw/master/doc/svgs/rendered_images/rich_table_tree.png)

[And here's the rich tree for the same more complicated NMAP cheat sheet PDF linked instead of shown directly in the previous section](doc/svgs/rendered_images/NMAP_Commands_Cheat_Sheet_and_Tutorial.pdf.rich_table_tree.png).


## Fonts

#### **Extract character mappings from ancient Adobe font formats**. It's actually `PyPDF` doing the lifting here but we're happy to take the credit.

![](https://github.com/michelcrypt4d4mus/pdfalyzer/raw/master/doc/svgs/rendered_images/font_character_mapping.png)


#### **View the properties of the fonts in the PDF**. Comes with a preview of the beginning and end of the font's raw binary data stream (if it's that kind of font).

![](https://github.com/michelcrypt4d4mus/pdfalyzer/raw/master/doc/svgs/rendered_images/font_summary_with_byte_preview.png)


## Binary Analysis (And Lots Of It)

### **YARA Scan:** Check PDF for malicious content.
This repo contains [all the PDF specific YARA rules I could dig up](pdfalyzer/yara_rules) that identify byte patterns indicating a PDF may have been modified for evil. While the real dangers exist in PDF modifications no one has seen yet (and thus we have no YARA rules for), there are still a bunch of 'sus' indicators (e.g. has a Type1 font, is incorrectly terminated, etc.) that will be tripped when you scan a PDF with The Pdfalyzer.

![](https://github.com/michelcrypt4d4mus/pdfalyzer/raw/master/doc/svgs/rendered_images/yara_matches.png)

### **Search Internal Binary Data for Sus Content No Malware Scanner Will Catch[^6]:**
Things like, say, a hidden binary `/F` (PDF instruction meaning "URL") followed by a `JS` (I'll let you guess what "JS" stands for) and then a binary `»` character (AKA "the character the PDF specification uses to close a section of the PDF's logical structure"). Put all that together and it says that you're looking at a secret JavaScript instruction embedded in the encrypted part of a font binary. A secret instruction that causes the PDF renderer to pop out of its frame prematurely as it renders the font.

![](https://github.com/michelcrypt4d4mus/pdfalyzer/raw/master/doc/svgs/rendered_images/font29.js.1.png)

### **Extract And Decode Binary Patterns:** Like, say, bytes between common regular expression markers that you might want to force a decode of in a lot of different encodings.

![](https://github.com/michelcrypt4d4mus/pdfalyzer/raw/master/doc/svgs/rendered_images/font_34_frontslash_scan.png)

### **See stats:** When all is said and done you can see some stats that may help you figure out what the character encoding may or may not be for the bytes matched by those patterns:

![](https://github.com/michelcrypt4d4mus/pdfalyzer/raw/master/doc/svgs/rendered_images/font29_summary_stats.png)


### **Fancy Table To Tell You What The `chardet` Library Would Rank As The Most Likely Encoding For A Chunk Of Binary Data**

![](https://github.com/michelcrypt4d4mus/pdfalyzer/raw/master/doc/svgs/rendered_images/decoding_and_chardet_table_2.png)

-------------

# PDF Resources
## Included PDF Tools
The Pdfalyzer ships with a command line tool `combine_pdfs` that combines multiple PDFs into a single PDF. Run `combine_pdfs --help` to see the options.

## 3rd Party PDF Tools
### Installing Didier Stevens's PDF Analysis Tools
Stevens's tools provide comprehensive info about the contents of a PDF, are guaranteed not to trigger the rendering of any malicious content (especially `pdfid.py`), and have been battle tested for well over a decade. It would probably be a good idea to analyze your PDF with his tools before you start working with this one.

If you're lazy and don't want to retrieve his tools yourself there's [a simple bash script](scripts/install_didier_stevens_pdf_tools.sh) to download them from his github repo and place them in a `tools/` subdirectory off the project root. Just run this:

```sh
scripts/install_didier_stevens_pdf_tools.sh
```

If there is a discrepancy between the output of betweeen his tools and this one you should assume his tool is correct and The Pdfalyzer is wrong until you conclusively prove otherwise.

### Installing The `t1utils` Font Suite
`t1utils` is a suite of old but battle tested apps for manipulating old Adobe font formats.  You don't need it unless you're dealing with an older Type 1 or Type 2 font binary but given that those have been very popular exploit vectors in the past few years it can be extremely helpful. One of the tools in the suite, [`t1disasm`](https://www.lcdf.org/type/t1disasm.1.html), is particularly useful because it decrypts and decompiles Adobe Type 1 font binaries into a more human readable string representation.

There's [a script](scripts/install_t1utils.sh) to help you install the suite if you need it:

```sh
scripts/install_t1utils.sh
```

## External Documentation
### Official Adobe Documentation
* [Official Adobe PDF 1.7 Specification](https://opensource.adobe.com/dc-acrobat-sdk-docs/standards/pdfstandards/pdf/PDF32000_2008.pdf) - Indispensable map when navigating a PDF forest.
* [Adobe Type 1 Font Format Specification](https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf) - Official spec for Adobe's original font description language and file format. Useful if you have suspicions about malicious fonts. Type1 seems to be the attack vector of choice recently which isn't so surprising when you consider that it's a 30 year old technology and the code that renders these fonts probably hasn't been extensively tested in decades because almost no one uses them anymore outside of people who want to use them as attack vectors.
* [Adobe CMap and CIDFont Files Specification](https://adobe-type-tools.github.io/font-tech-notes/pdfs/5014.CIDFont_Spec.pdf) - Official spec for the character mappings used by Type1 fonts / basically part of the overall Type1 font specification.
* [Adobe Type 2 Charstring Format](https://adobe-type-tools.github.io/font-tech-notes/pdfs/5177.Type2.pdf) - Describes the newer Type 2 font operators which are also used in some multiple-master Type 1 fonts.

### Other Stuff
* [Didier Stevens's PDF tools](http://blog.didierstevens.com/programs/pdf-tools/)
* [Didier Stevens's free book about malicious PDFs](https://blog.didierstevens.com/2010/09/26/free-malicious-pdf-analysis-e-book/) - The master of the malicious PDFs wrote a whole book about how to analyze them. It's an old book but the PDF spec was last changed in 2008 so it's still relevant.
* [Analyzing Malicious PDFs Cheat Sheet](https://zeltser.com/media/docs/analyzing-malicious-document-files.pdf) - Like it says on the tin. If that link fails there's a copy [here in the repo](doc/analyzing-malicious-document-files.pdf).
* [T1Utils Github Repo](https://github.com/kohler/t1utils) - Suite of tools for manipulating Type1 fonts.
* [`t1disasm` Manual](https://www.lcdf.org/type/t1disasm.1.html) - Probably the most useful part of the T1Utils suite because it can decompile encrypted ancient Adobe Type 1 fonts into something human readable.
* [PDF Flaws 101](https://github.com/RUB-NDS/PDF101) from Black Hat 2020.
* [A Curious Exploration of Malicious PDF Documents](https://www.scitepress.org/Papers/2020/89923/89923.pdf) by Julian Lindenhofer, Rene Offenthaler and Martin Pirker, 2020. Overview of all the possible execution paths that can lead to a PDF executing JavaScript, opening loca/remote files, or making web requests.
* [Malicious PDF Generator](https://github.com/jonaslejon/malicious-pdf) is a well maintained GitHub project that does what it says on the tin.
* [PDF is Broken, and so is this file](https://blog.trailofbits.com/2021/02/02/pdf-is-broken-a-justctf-challenge/) is a 2021 report on what happens when you challenge cybersecurity teams to turn PDFs into weapons. (Among other things they managed to create a PDF that launches a webserver when you open it.)
* [linuxPDF](https://github.com/ading2210/linuxpdf) is a project that managed to embed an entire linux operating system inside a PDF document. The related [DoomPDF](https://github.com/ading2210/doompdf) managed to embed the classic video game Doom in a PDF.
* [horrifying-pdf-experiments](https://github.com/osnr/horrifying-pdf-experiments) is a repo of horrifying things you can do with PDFs.


## Did The World Really Need Another PDF Tool?
This tool was built to fill a gap in the PDF assessment landscape following [my own recent experience trying to find malicious content in a PDF file](https://twitter.com/Cryptadamist/status/1570167937381826560). Didier Stevens's [pdfid.py](https://github.com/DidierStevens/DidierStevensSuite/blob/master/pdfid.py) and [pdf-parser.py](https://github.com/DidierStevens/DidierStevensSuite/blob/master/pdf-parser.py) are still the best game in town when it comes to PDF analysis tools but they lack in the visualization department and also don't give you much to work with as far as giving you a data model you can write your own code around. [Peepdf](https://github.com/jesparza/peepdf) seemed promising but turned out to be in a buggy, out of date, and more or less unfixable state. And neither of them offered much in the way of tooling for embedded binary analysis.

Thus I felt the world might be slightly improved if I strung together a couple of more stable/well known/actively maintained open source projects ([AnyTree](https://github.com/c0fec0de/anytree), [PyPDF](https://github.com/py-pdf/pypdf), [Rich](https://github.com/Textualize/rich), and [YARA](https://github.com/VirusTotal/yara-python) via [The Yaralyzer](https://github.com/michelcrypt4d4mus/yaralyzer)) into this tool.

-------------

# Contributing
One easy way of contributing is to run [the script to test against all the PDFs in your `~/Documents` folder](scripts/test_against_all_pdfs_in_Documents_folder.sh) and report any issues.

Beyond that see [CONTRIBUTING.md](CONTRIBUTING.md).

### Code Glossary
These are the naming conventions at play in The Pdfalyzer code base:

| Term  | Meaning |
| ----------------- | ---------------- |
| **`PDF Object`** | Instance of a `PyPDF` class that represents the information stored in the PDF binary between open and close guillemet quotes (« and ») |
| **`reference_key`** | String found in a PDF object that names a property (e.g. `/BaseFont` or `/Subtype`) |
| **`reference`** | Link _from_ a PDF object _to_ another node. Outward facing relationships, basically. |
| **`address`** | `reference_key` plus a hash key or numerical array index if that's how the reference works. e.g. if node A has a reference key `/Resources` pointing to a dict `{'/Font2': [IndirectObject(55), IndirectObject(2)]}` the address of `IndirectObject(55)` from node A would be `/Resources[/Font2][0]` |
| **`tree_address`** | Like the `address` but starting at the root of the tree. Describes the series of objects you would step through if you walked the tree from the root to this node. |
| **`relationship`** | Any link between nodes created by addresses/reference keys |
| **`non_tree_relationship`** | any link between nodes that is not considered a parent/child tree relationship |
| **`indeterminate_node`** | any node whose place in the tree cannot be decided until every node has been seen |
| **`link_node`** | nodes like `/Dest` that just contain a pointer to another node |

### Reference
* [`PyPDF` documentation](https://pypdf.readthedocs.io/en/stable/) (latest is 4.x or something so these are the relevant docs for `pdfalyze`)


# TODO
* Highlight decodes with a lot of Javascript keywords
* https://github.com/mandiant/flare-floss (https://github.com/mandiant/flare-floss/releases/download/v2.1.0/floss-v2.1.0-linux.zip)
* https://github.com/1Project/Scanr/blob/master/emulator/emulator.py


[^1]: The official Adobe PDF specification calls this tree the PDF's "logical structure", which is a good example of nomenclature that does not help those who see it understand anything about what is being described. I can forgive them given that they named this thing back in the 80s, though it's a good example of why picking good names for things at the beginning is so important.

[^2]: An exception will be raised if there's any issue placing a node while parsing or if there are any nodes not reachable from the root of the tree at the end of parsing. If there are no exceptions then all internal PDF objects are guaranteed to exist in the tree except in these situations when warnings will be printed:
  `/ObjStm` (object stream) is a collection of objects in a single stream that will be unrolled into its component objects.
  `/XRef` Cross-reference stream objects which hold the same references as the `/Trailer` are hacked in as symlinks of the `/Trailer`

[^3]: Given the nature of the PDFs this tool is meant to be scan anything resembling "rendering" the document is pointedly NOT offered.

[^4]: `pipx` is a tool that basically runs `pip install` for a python package but in such a way that the installed package's requirements are isolated from your system's python packages. If you don't feel like installing `pipx` then `pip install` should work fine as long as there are no conflicts between The Pdfalyzer's required packages and those on your system already. (If you aren't using other python based command line tools then your odds of a conflict are basically 0%.)

[^5]: Technically they are `SymlinkNodes`, a really nice feature of [AnyTree](https://github.com/c0fec0de/anytree).

[^6]: At least they weren't catching it as of September 2022.
