# THE PDFALYZER
A PDF analysis tool geared towards visualizing the inner tree-like data structure[^1] of a PDF in [spectacularly large and colorful diagrams](#example-output) as well as scanning the various kinds of binary data within the PDF for hidden potentially malicious content.

**PyPi Users:** If you are reading this `README` on PyPi be aware that it renders a lot better - with footnotes, images, etc. - [over on GitHub](https://github.com/michelcrypt4d4mus/pdfalyzer)).

[^1]: The official Adobe PDF specification calls this tree the PDF's "logical structure", which is a good example of nomenclature that does not help those who see it understand anything about what is being described. I can forgive them given that they named this thing back in the 80s, though it's a good example of why picking good names for things at the beginning is so important.

### What It Do
1. **Generate summary format as well as in depth visualizations of a PDF's tree structure**[^1] with helpful color themes that conceptually link objects of similar type. See [the examples below](#example-output) to get an idea.
1. **Display text representations of the PDF's embedded binary data**. Adobe calls these "streams" and they hold things like images, fonts, etc.
1. **Scan for malicious content in the PDF**, including in-depth scans of the embedded font binaries where other tools don't look. This is accomplished by iterating over all the matches for various predefined binary regexes (e.g. the binary representation of the string `/JavaScript`) but is extensible to digging through the PDF for any kind of binary data pattern.
1. **Be used as a library for your own PDF related code.** All[^2] the inner PDF objects are guaranteed to be available in a searchable tree data structure.
1. **Ease the extraction of all the binary data in a PDF** (fonts, images, etc) to separate files for further analysis. (The heavy lifting is actually done by [Didier Stevens's tools](#installing-didier-stevenss-pdf-analysis-tools) - the pdfalyzer automates what would otherwise be a lot of typing into a single command.)

If you're looking for one of these things this may be the tool for you.

An exception will be raised if there's any issue placing a node while parsing or if there are any nodes not reachable from the root of the tree at the end of parsing.

[^2]: All internal PDF objects are guaranteed to exist in the tree except in these situations when warnings will be printed:
  `/ObjStm` (object stream) is a collection of objects in a single stream that will be unrolled into its component objects.
  `/XRef` Cross-reference stream objects which hold the same references as the `/Trailer` are hacked in as symlinks of the `/Trailer`

### What It Don't Do
This tool is mostly about examining a PDF's logical structure and assisting with the discovery of malicious content. As such it doesn't have much to offer as far as extracting text from PDFs, rendering PDFs[^3], writing new PDFs, or many of the more conventional things one might do with a portable document.

[^3]: Given the nature of the PDFs this tool is meant to be scan anything resembling "rendering" the document is pointedly NOT offered.

### Did The World Really Need Another PDF Tool?
This tool was built to fill a gap in the PDF assessment landscape following my . Didier Stevens's [pdfid.py](https://github.com/DidierStevens/DidierStevensSuite/blob/master/pdfid.py) and [pdf-parser.py](https://github.com/DidierStevens/DidierStevensSuite/blob/master/pdf-parser.py) are still the best game in town when it comes to PDF analysis tools but they lack in the visualization department and also don't give you much to work with as far as giving you a data model you can write your own code around. [Peepdf](https://github.com/jesparza/peepdf) seemed promising but turned out to be in a buggy, out of date, and more or less unfixable state. And neither of them offered much in the way of tooling for embedded font analysis.

All those things being the case lead to a situation where I felt the world might be slightly improved if I strung together a couple of more stable/well known/actively maintained open source projects ([AnyTree](https://github.com/c0fec0de/anytree), [PyPDF2](https://github.com/py-pdf/PyPDF2), and [Rich](https://github.com/Textualize/rich)) into this tool.

### OK Let's Do This
See [Installation](#installation) and [Usage](#usage) below (past the enormous images showing example output).



# Example Output
`pdfalyzer` can export visualizations to HTML, ANSI colored text, and SVG images using the file export functionality that comes with [Rich](https://github.com/Textualize/rich). SVGs can be turned into `png` format images with a tool like `inkscape` or `cairosvg` (Inkscape works a lot better in our experience).


### Basic Tree View
As you can see the "mad sus" `/OpenAction` relationship is highlighted bright red, as would be a couple of other suspicious PDF instructions like `/JavaScript` that don't exist in the PDF but do exist in other documents.

The dimmer (as in "harder to see") nodes[^4] marked with `Non Child Reference` give you a way to visualize the relationships between PDF objects that exist outside of the tree structure's parent/child relationships.

![Basic Tree](doc/svgs/rendered_images/basic_tree.png)

That's a pretty basic document. If you'd like to see the tree for a more complicated/longer PDF, [here's an example showing the `nmap` cheat sheet](doc/svgs/rendered_images/NMAP_Commands_Cheat_Sheet_and_Tutorial.pdf.tree.svg.png).

[^4]: Technically they are `SymlinkNodes`, a really nice feature of [AnyTree](https://github.com/c0fec0de/anytree).

### Rich Tree View
This image shows a more in-depth view of of the PDF tree for the same document shown above. This tree (AKA the "rich" tree) has almost everything - shows all PDF object properties, all relationships between objects. Even includes sizable previews of any binary data streams embedded or encrypted in the document. Note that the `/OpenAction` is highlighted in bright red, as is the Adobe Type1 font binary (Google's project zero regards any Adobe Type1 font as "mad sus").

[Here's an even bigger example showing the same `nmap` cheat sheet](doc/svgs/rendered_images/NMAP_Commands_Cheat_Sheet_and_Tutorial.pdf.rich_table_tree.png).

![Rich Tree](doc/svgs/rendered_images/rich_table_tree.png)

### Font Analysis (And Lots Of It)
#### View the Properties of the Fonts in the PDF
Comes with a preview of the beginning and end of the font's raw binary data stream (at least if it's that kind of font).

![Font Properties](doc/svgs/rendered_images/font_summary_with_byte_preview.png)

#### Extract Character Mappings from Ancient Adobe Font Formats
It's actually `PyPDF2` doing the lifting here but we're happy to take the credit.

![Font Charmap](doc/svgs/rendered_images/font_character_mapping.png)

#### Search Encrypted Binary Font Data for #MadSus Content No Malware Scanner Will Catch[^5]

doc/svgs/rendered_images/font_24_binary_scan.png

Things like, say, a hidden binary `/F` (PDF instruction meaning "URL") followed by a `JS` (I'll let you guess what "JS" stands for) and then a binary `»` character (AKA "the character the PDF specification uses to close a section of the PDF's logical structure"). Put all that together and it says that you're looking at a secret JavaScript instruction embedded in the encrypted part of a font binary. A secret instruction that causes the PDF renderer to pop out of its frame prematurely as it renders the font.

![Font with JS](doc/svgs/rendered_images/font29.js.1.png)

#### Extract And Decode Binary Patterns
Like, say, bytes between common regular expression markers that you might want to force a decode of in a lot of different encodings.
![Font Scan Regex](doc/svgs/rendered_images/font_34_frontslash_scan.png)

When all is said and done you can see some stats that may help you figure out what the character encoding may or may not be for the bytes matched by those patterns:
![Font Decode Summary](doc/svgs/rendered_images/font29_summary_stats.png)


[^5]: At least they weren't catching it as of September 2022.

#### Now There's Even A Fancy Table To Tell You What The `chardet` Library Would Rank As The Most Likely Encoding For A Chunk Of Binary Data
Behold the beauty:
![Basic Tree](doc/svgs/rendered_images/decoding_and_chardet_table_2.png)

### Compute Summary Statistics About A PDF's Inner Structure
Some simple counts of some properties of the internal PDF objects. Not the most exciting but sometimes helpful. `pdfid.py` also does something much like this. Not exciting enough to show a screenshot.


# Installation
```
pip install pdfalyzer
```
For info on how to setup a dev environment, see [Contributing](#contributing) section at the end of this file.

### Troubleshooting The Installation
1. If you encounter an error building the python `cryptography` package check your `pip` version (`pip --version`). If it's less than 22.0, upgrade `pip` with `pip install --upgrade pip`.
2. On linux if you encounter an error building `wheel` or `cffi` you may need to install some packages like a compiler for the `rust` language or some SSL libraries. `sudo apt-get install build-essential libssl-dev libffi-dev rustc` may help.
1. While `poetry.lock` is checked into this repo the versions "required" there aren't really "required" so feel free to delete or downgrade if you need to.

### 3rd Party Tools
#### Installing Didier Stevens's PDF Analysis Tools
Stevens's tools provide comprehensive info about the contents of a PDF, are guaranteed not to trigger the rendering of any malicious content (especially `pdfid.py`), and have been battle tested for well over a decade. It would probably be a good idea to analyze your PDF with his tools before you start working with this one.

If you're lazy and don't want to retrieve his tools yourself there's [a simple bash script](scripts/install_didier_stevens_pdf_tools.sh) to download them from his github repo and place them in a `tools/` subdirectory off the project root. Just run this:

```sh
scripts/install_didier_stevens_pdf_tools.sh
```

If there is a discrepancy between the output of betweeen his tools and this one you should assume his tool is correct and `pdfalyzer` is wrong until you conclusively prove otherwise.

#### Installing The `t1utils` Font Suite
`t1utils` is a suite of old but battle tested apps for manipulating old Adobe font formats.  You don't need it unless you're dealing with an older Type 1 or Type 2 font binary but given that those have been very popular exploit vectors in the past few years it can be extremely helpful. One of the tools in the suite, [`t1disasm`](https://www.lcdf.org/type/t1disasm.1.html), is particularly useful because it decrypts and decompiles Adobe Type 1 font binaries into a more human readable string representation.

There's [a script](scripts/install_t1utils.sh) to help you install the suite if you need it:

```sh
scripts/install_t1utils.sh
```



# Usage
2. Run `pdfalyze -h` to see usage instructions.

As of right now these are the options:

![argparse_help](doc/screenshots/rich_help/full_text_of_help_orange_group.png)

**There's some further exposition on the particulars of what these options mean in [the sample `.pdfalyzer` file](.pdfalyzer.example).** Even if don't configure your own `env` you may still glean some insight from reading the descriptions of the various environment variables.

Beyond that there's [a few scripts](scripts/) in the repo that may be of interest.

### Setting Command Line Options Permanently With A `.pdfalyzer` File
If you find yourself specificying the same options over and over you may be able to automate that with a [dotenv](https://pypi.org/project/python-dotenv/) setup. Documentation on the available configuration options lives in [`.pdfalyzer.example`](.pdfalyzer.example) which doubles as a file you can copy into place and edit to your heart's content.

```sh
cp .pdfalyzer.example .pdfalyzer
```


### As A Code Library
The `Pdfalyzer` class is the core of the operation as it holds both the PDF's logical tree as well as a couple of other data structures that have been pre-processed to make them easier to work with. Chief among these is the `FontInfo` class which pulls together various properties of a font strewn across 3 or 4 different PDF objects.


Here's how to get at these objects:

```python
from pdfalyzer.pdfalyzer import Pdfalyzer

# Load a PDF and parse its nodes into the tree.
walker = Pdfalyzer("/path/to/the/evil.pdf")
actual_pdf_tree = walker.pdf_tree

# Find a PDF object by its ID in the PDF
node = walker.find_node_by_idnum(44)
pdf_object = node.obj

# Use anytree's findall_by_attr to find nodes with a given property
from anytree.search import findall_by_attr
page_nodes = findall_by_attr(walker.pdf_tree, name='type', value='/Page')

# Get the fonts
font1 = walker.font_infos[0]

# Iterate over backtick quoted strings from a font binary and process them
for backtick_quoted_string in font1.binary_scanner.extract_backtick_quoted_bytes():
    process(backtick_quoted_string)

# Try to decode - by force if necessary - everything in the font binary that looks like a quoted string
# or regex (meaning bytes between single quotes, double quotes, front slashes, backticks, or guillemet quotes)
font1.force_decode_all_quoted_bytes()
```

The binary stream data search and forced decoding options are not limited to font binaries and indeed can work with any binary data in the form of a `bytes` or `bytearray` primitive.

```python
from pdfalyzer.binary.binary_scanner import BinaryScanner

binary_scanner = BinaryScanner(some_bytes: bytes)

# Iterate over regions around bytes that match an arbitrary byte pattern (returned object includes surrounding bytes)
for regex_match in binary_scanner.extract_regex_capture_bytes(re.compile(b'\xa0\xcc\xdd\xfa')):
    process_(regex_match)

# If you provide a capture group you will be returned an object that separates the capture group from the region
for regex_match in binary_scanner.extract_regex_capture_bytes(re.compile(b'\xcc(.*)\xdd')):
    process_(regex_match)
```

The representation of the PDF objects (e.g. `pdf_object` in the example above) is handled by [PyPDF2](https://github.com/py-pdf/PyPDF2) so for more details on what's going on there check out its documentation.

### Troubleshooting
This tool is by no means complete. It was built to handle a specific use case which encompassed a small fraction of the many and varied types of information that can show up in a PDF. While it has been tested on a decent number of large and very complicated PDFs (500-5,000 page manuals from Adobe itself) I'm sure there are a whole bunch of edge cases that will trip up the code.

If that does happen and you run into an issue using this tool on a particular PDF it will most likely be an issue with relationships between objects within the PDF that are not meant to be parent/child in the tree structure made visible by this tool. There's not so many of these kinds of object references in any given file but there's a whole galaxy of possibilities and they must each be manually configured to prevent the tool from building an invalid tree.  If you run into that kind of problem take a look at these list constants in the code:

* `NON_TREE_REFERENCES`
* `INDETERMINATE_REFERENCES`

You might be able to easily fix your problem by adding the Adobe object's reference key to the appropriate list.



# PDF Resources
#### Official Adobe Documentation
* [Official Adobe PDF 1.7 Specification](https://opensource.adobe.com/dc-acrobat-sdk-docs/standards/pdfstandards/pdf/PDF32000_2008.pdf) - Indispensable map when navigating a PDF forest.
* [Adobe Type 1 Font Format Specification](https://adobe-type-tools.github.io/font-tech-notes/pdfs/T1_SPEC.pdf) - Official spec for Adobe's original font description language and file format. Useful if you have suspicions about malicious fonts. Type1 seems to be the attack vector of choice recently which isn't so surprising when you consider that it's a 30 year old technology and the code that renders these fonts probably hasn't been extensively tested in decades because almost no one uses them anymore outside of people who want to use them as attack vectors.
* [Adobe CMap and CIDFont Files Specification](https://adobe-type-tools.github.io/font-tech-notes/pdfs/5014.CIDFont_Spec.pdf) - Official spec for the character mappings used by Type1 fonts / basically part of the overall Type1 font specification.
* [Adobe Type 2 Charstring Format](https://adobe-type-tools.github.io/font-tech-notes/pdfs/5177.Type2.pdf) - Describes the newer Type 2 font operators which are also used in some multiple-master Type 1 fonts.

#### Other Stuff
* [Didier Stevens's free book about malicious PDFs](https://blog.didierstevens.com/2010/09/26/free-malicious-pdf-analysis-e-book/) - The master of the malicious PDFs wrote a whole book about how to analyze them. It's an old book but the PDF spec was last changed in 2008 so it's still relevant.
* [Analyzing Malicious PDFs Cheat Sheet](https://zeltser.com/media/docs/analyzing-malicious-document-files.pdf) - Like it says on the tin. If that link fails there's a copy [here in the repo](doc/analyzing-malicious-document-files.pdf).
* [T1Utils Github Repo](https://github.com/kohler/t1utils) - Suite of tools for manipulating Type1 fonts.
* [`t1disasm` Manual](https://www.lcdf.org/type/t1disasm.1.html) - Probably the most useful part of the T1Utils suite because it can decompile encrypted ancient Adobe Type 1 fonts into something human readable.



# Contributing
One easy way of contributing is to run [the script to test against all the PDFs in `~/Documents`](scripts/test_against_all_pdfs_in_Documents_folder.sh) and reporting any issues.

Beyond that contributions are welcome, just make sure that before you open a pull request:

1. The test suite passes (run by typing `pytest`)
1. You add a description of your changes to [the changelog](CHANGELOG.md)

If your pull request includes some `pytest` setup/unit testing you'll be my new favorite person.

## Development Environment Setup
1. `git clone https://github.com/michelcrypt4d4mus/pdfalyzer.git`
1. `cd pdfalyzer`

After that there's a forking path depending on whether or not you use [poetry](https://python-poetry.org) to manage your python lifestyle.

Note that the minimum versions for each package were chosen because that's what worked on my machine and not because that version had some critical bug fix or feature so it's entirely possible that using earlier versions than are specified in [pyproject.toml](pyproject.toml) or [requirements.txt](requirements.txt) will work just fine. Feel free to experiment if there's some kind of version conflict for you.

#### With Python Poetry
These commands are the `poetry` equivalent of the traditional virtualenv installation followed by `source venv/bin/activate` but there's a lot of ways to run a python script in a virtualenv with `poetry` so you do you if you prefer another approach.

```sh
poetry install
source $(poetry env info --path)/bin/activate
```

#### With A Manual `venv`
```sh
python -m venv .venv              # Create a virtualenv in .venv
. .venv/bin/activate              # Activate the virtualenv
pip install -r requirements.txt   # Install packages
```

Note that I'm not sure exactly how to get the `pdfalyze` command installed when developing outside of a `poetry` env, but creating a simple `run_pdfalyzer.py` file with these contents would do the same thing:
```python
from pdfalyzer import pdfalyzer
pdfalyzer()
```

## Testing
Run all tests by typing `pytest`. Test coverage is relatively spartan but should throw failures if you really mess something up. See [How To Invoke pytest](https://docs.pytest.org/en/7.1.x/how-to/usage.html) official docs for other options.


# TODO
* highlight decodes done at `chardet`s behest
* Highlight decodes with a lot of Javascript keywords
* deal with repetitive matches
