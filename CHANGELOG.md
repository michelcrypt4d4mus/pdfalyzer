# NEXT RELEASE

### 1.16.9
* Add `Development Status :: 5 - Production/Stable` to pypi classifiers

### 1.16.8
* Even more PDF related YARA rules
* Upgrade `anytree` to 2.13.0
* Upgrade `yaralyzer` to 1.0.4

### 1.16.7
* Lots of new PDF related YARA rules
* Upgrade `yaralyzer` to 1.0.3
* Upgrade `pypdf` to 5.9.0

### 1.16.6
* Add the creator hash to GIFTEDCROOK rule

### 1.16.5
* Add YARA rule for GIFTEDCROOK infostealer PDFs

### 1.16.4
* Bump `PyPDF` to 5.7.0

### 1.16.3
* Fix typo in help

### 1.16.2
* Add two more PDF related YARA rules

### 1.16.1
* Configure a `Changelog` link for `pypi` to display

# 1.16.0
* Upgrade `PyPDF2` 2.x to `pypdf` 5.0.1 (new name, same package)
* Add `--image-quality` option to `combine_pdfs` tool

### 1.15.1
* Add `--no-default-yara-rules` command line option so users can use _only_ their own custom YARA rules files if they want. Previously you could only use custom YARA rules _in addition to_ the default rules; now you can just skip the default rules.

# 1.15.0
* Add `combine_pdfs` command line script to merge a bunch of PDFs into one
* Remove unused `Deprecated` dependency

### 1.14.10
* Add `malware_MaldocinPDF` YARA rule

### 1.14.9
* Add [ActiveMime YARA rule](https://blog.didierstevens.com/2023/08/29/quickpost-pdf-activemime-maldocs-yara-rule/)

### 1.14.8
* Handle internal YARA errors more gracefully with error messages instead of crashes (currently seeing `ERROR_TOO_MANY_RE_FIBERS` on macOS on some files for unknown reasons that we hope will go away eventually)

### 1.14.7
* Bump `yaralyzer` version to 0.9.4 (and thus bump `yara-python` to 4.3.0+)
* Remove unused imports, remove unused `requirements.txt` file.

### 1.14.6
* Fix issue where additional YARA rules supplied with `--yara-file` option were not being used

### 1.14.5
* Update PDF matching YARA rules file (@anotherbridge)

### 1.14.4
* Bump version for pypi tag / shield image (@MartinThoma)

### 1.14.3
* Bump version for release

### 1.14.2
* Bump `yaralyzer` version to handle `yara-python` breaking change

### 1.14.1
* Fix export filename

# 1.14.0
* Add `--preview-stream-length` option
* Store parsed `args` on `PdfalyzerConfig` class
* Yaralyzer CLI options all configurable with env vars.

### 1.13.2
* Fix infinite loop bug encountered when building some char maps

### 1.13.1
* Add **all** the possible PDF internal commands that can lead to JavaScript execution or local/remote command exection to `DANGEROUS_PDF_KEYS` list.

# 1.13.0
* New `--extract-quoted` argument can be specified to have `yaralyzer` extract and decode all bytes between the specified quote chars.
* Quoted bytes are no longer force decoded by default.
* New `--suppress-boms` argument suppresses BOM search.

### 1.12.3
* Fix PER ENCODING METRICS subtable in decodings stats table
* Add percentage calculations to decoding attempts table
* `--log-level` option (from `yaralyzer`)

### 1.12.2
* Refactor `PdfTreeVerifier` and `IndeterminateNode` out of `Pdfalyzer` class

### 1.12.1
* Check for any explicit `/Kids` relationships when placing indeterminate nodes
* All other things being equal prefer a single `/Page` or `/Pages` referrer as the parent

# 1.12.0
* Rich table view displays object properties and referenced nodes with appropriate color and labeling
* Style `/Encoding` objects as part of the font family
* Refactor text coloring/styling to `pdfalyzer.output.styles` package

### 1.11.6
* Launchable with `python -m pdfalyzer` for those who can't get `pdfalyze` script to work (h/t @MartinThoma)

### 1.11.5
* Last ditch attempt to place indeterminate nodes according to which node has most descendants catches almost everything
* Refactor `PdfalyzerPresenter` class to handle output formatting.

### 1.11.4
* Fix parent/child issue with `/Annots` arrays being indeterminate
* Fix issue with `/ColorSpace` node placement

### 1.11.3
* Add `sub_type` to node label
* Handle unsupported stream filters (e.g. `/JBIG2Decode`) more gracefully
* Suppress spurious warnings about multiple refs
* Handle edge case `/Resources` node placement
* Refactor `pdf_object_properties.py` decorator
* Show embedded streams table in `--docinfo` output
* Unify indeterminate node tree placement logic (`/Resources` are not special)

### 1.11.2
* Bump dependencies

### 1.11.1
* Fix regressions
* Fix issue when `/Resources` is referred to by multiple addresses from different nodes

# 1.11.0
* Scan all binaries (not just font binaries) with included PDF related YARA rules
* Better warning about stream decode failures
* Remove warnings that should not be warnings
* Refactor rich table view code to `pdf_node_rich_table.py`
* Refactor `Relationship` and `PdfObjectRef` to single class, `PdfObjectRelationship`

### 1.10.8
* Fix `importlib.resources` usage in case pdfalyer is packaged as a zip file
* `/Names` is an indeterminate reference type
* Catch stream decode exceptions and show error instead of failing.

### 1.10.7
* Improve the handling of ColorSpace and Resources nodes

### 1.10.6
* Improve the handling of indeterminate and pure reference nodes (again)

### 1.10.5
* Improve the handling of indeterminate and pure reference nodes

### 1.10.4
* Fix bug with unescaped string in section header

### 1.10.3
* Fix bug with discovery of packaged `.yara` files
* More PDF YARA rules from `lprat`

### 1.10.2
* Bump deps

### 1.10.1
* Use `rich_argparse_plus` for help text

# 1.10.0
* `--streams` arg now takes an optional PDF object ID
* `--fonts` no longer takes an optional PDF object ID
* YARA matches will display more than 512 bytes
* Improved output formatting

# 1.9.0
* Scan all binary streams, not just fonts.  Separate `--streams` option is provided. (`--font` option has much less output)
* Display MD5, SHA1, and SHA256 for all binary streams as well as overall file

### 1.8.3
* Highlight suspicious instructions in red, BOMs in green
* Reenable guillemet quote matching
* Clearer labeling of binary scan results
* Sync with `yaralyzer` v0.4.0

### 1.8.2
* Sync with `yaralyzer` v0.3.3

### 1.8.1
* Show defaults and valid values for command line options

# 1.8.0
* Add table of stream lengths for PDF objects containing streams to `--doc-info` output
* Quote extraction API methods should use yara, not bespoke extraction
* Fix bug with rich tree view of non binary streams

# 1.7.0
* Use `yaralyzer` as the match engine
* Scan all binary streams, not just the fonts

# 1.6.0
* Integrate YARA scanning - all the rules I could dig up relating to PDFs
* Add MD5, SHA1, SHA256 to document info section
* `pdfalyzer_show_color_theme` script shows the theme
* Make `README` more PyPi friendly

# 1.5.0
Bunch of small changes to support releasing on [pypi](https://pypi.org/project/pdfalyzer/)
* Invoke with shell command `pdfalyze` instead of local python file `./pdfalyzer.py` (options are the same)
* Core class renames: `PdfWalker` -> `Pdfalyzer`, `DataStreamHandler` -> `BinaryScanner`
* Permanent env var configuration moved from a file called `.env` to a file called `.pdfalyzer`
* Logging to a file is off unless configured by env var
* To use Didier Stevens's `pdf-parser.py` you must provide the `PDFALYZER_PDF_PARSER_PY_PATH` env var

# 1.4.0
* Hexadecimal representation of matched bytes in decode attempts table
* `--quote-type` option to limit binary scans
* `--min-decode-length` option to skip decode attempts on short matches
* `--file-suffix` option
* Output filenames will contain some of the options used to generate them
* Add runtime params to export filenames where it is material to the output
* Ensure `/OpenAction` etc are not subsumed by parent/child relationships in the condensed tree view
* Tweak available configuration options for logging to file.

# 1.3.1
* Fix bug with validating directly embedded objects

# 1.3.0
### General
* Improved scanning of binaries for `UTF-X` encoded data where X is not a prime number.
* Lots of summary data is now displayed about what were the most and least successful encodings at extracting some meaning (or at least not failing) from binary sequences surrounded by quote chars, frong slashes, backticks, etc etc.
* Will execute "by the book" decodes using normally untested encodings if the `chardet.detect()` library feels strongly enough about it.
* Exporting SVGs, HTML, and colored text can be done in a single invocation.

### Logging
* Invocations of the tool are now logged in a history file `log/pdfalyzer.invocation.log`
* Logging to a file can be enabled by setting a `PDFALYZER_LOG_DIR` environment variable but see comments in `.pdfalyzer.example` about side effects.

### Command line options
* `--maximize-width` arg means you can set yr monitor to teeny tiny fonts and print out absolutely monstrous SVGs (yay!)
* `--chardet-cutoff` option lets you control the the cutoff for adding untested encodings to the output based on what `chardet.detect()` thinks is the right encoding
* `--suppress-chardet` command line option removes the chardet tables that are (mostly) duplicative of the decoded text tables
* `--output-dir` and `--file-prefix` are now shared by all the export modes
* You can use `dotenv` to permanently turn on or off or change the value of some command line options; see  [`.pdfalyzer.example`](.pdfalyzer.example) for mdetails on what is configurable.

### Visualizations
* Default `TerminalTheme` colors kind of sucked when you went to export SVGs and HTML... like black was not black, or even close. Things are simpler now - black is black, blue is blue, etc. Makes exports look better.

### Bugfixes
* Binary data highlighting now goes all the way to the end of the matched string in most cases (small bug had it falling 1-4 chars behind sometimes)
* Fix small bug with exporting font/binary details to SVGs
* Fix `Win-
* `BytesMatch` class to keep track of binary regex matches
* Group suppression notifications together



# 1.2.0
* Dramatic expansion in the `pdfalyzer`'s binary data scouring capabilities:
   * Add `chardet` library guesses as to the encoding of all unknown byte sequences and ranks them from most to least likely
   * Add attempted decodes of all backtick, frontslash, single, double, and guillemet quoted strings in font binaries
   * Add decode attempts with `Windows-1252`, `UTF-7`, and `UTF-16` encodings
   * Add `--suppress-decodes` to suppress attempted decodes of quoted strings in font binaries
   * Cool art gets generated when you swarm a binaries quoted strings, which are mostly but not totally random
* The `--font` option takes an optional argument to limit the output to a single font ID
* Add `--max-decode-length` to suppress attempted decodes of quoted strings in font binaries over a certain length
* Add `--surrounding` option to specify number of bytes to print/decode before and after suspicious bytes; decrease default number of surrounding bytes
* Add `--version` option
* `extract_guillemet_quoted_bytes()` and `extract_backtick_quoted_bytes()` are now iterators
* Fix scanning for `UTF-16` BOM in font binary

# 1.1.0
* Print unprintable ascii characters in the font binary forced decode attempt with a bracket notation. e.g. print the string `[BACKSPACE]` instead of deleting the previous character
* Add an attempt to decode font binary as `latin-1` in addition to `utf-8`
* Highlight the suspicious bytes in the font binary forced decode attempts
* Fix printing of suspicious font bytes when suspicions are near start or end of stream

# 1.0.2
* Color `/Widths` tables
* Color `/Catalog` and other summary nodes with with green
* Color `ByteStringObject` like bytes
* Resolve types of `IndirectObject` refs appearing in `dict` and `list` value Rich Tree table rows
* Remove redundant `/First` and `/Last` non tree refs when those relationships are part of the tree
* Couple of edge case bug fixes

# 1.0.1
* Fix issue with directly embedded `/Resources` not being walked correctly (along with their fonts)
* Introduce `PdfObjectRelationship` tuple to contain the root reference key, the actual reference address string, and the referenced obj
* Add warnings if any PDF objects are missing from the tree

# 1.0.0
* Initial release
* Change command line option style (capital letters for debugging, 3 letter codes for export)
* No need to explicitly call `walk_pdf()`
* Fix parent/child relationships for `/StructElem`
