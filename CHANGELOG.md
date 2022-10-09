# NEXT RELEASE

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
* Introduce `PdfObjectRef` tuple to contain the root reference key, the actual reference address string, and the referenced obj
* Add warnings if any PDF objects are missing from the tree

# 1.0.0
* Initial release
* Change command line option style (capital letters for debugging, 3 letter codes for export)
* No need to explicitly call `walk_pdf()`
* Fix parent/child relationships for `/StructElem`
