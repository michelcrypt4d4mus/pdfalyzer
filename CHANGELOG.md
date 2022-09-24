# 1.3.0
* Improved scanning of binaries for `UTF-X` encoded data, where X is not a prime number.
* You can use `dotenv` to permanently turn on or off or change the value of some command line options; see  [`.env.example`](.env.example) for mdetails on what is configurable.
* Invocations of the tool are now logged in a kind of history file - `pdfalyzer.invocation.log`
* `--maximize-width` arg means you can set yr monitor to teeny tiny fonts and print out absolutely monstrous SVGs (yay!)
* Default `TerminalTheme` colors kind of sucked when you went to export SVGs and HTML... like black was not black, or even close. Things are simpler now - black is black, blue is blue, etc. Makes exports look better.
* Lots of summary data about what were the most and least successful encodings at extracting some meaning (or at least not failing) when sifting through binary sequences surrounded by quote chars, frong slashes, backticks, etc etc.
* Will execute "by the book" decodes if the `chardet` library feels strongly enough about a given chunk of binary
* Binary data highlighting now goes all the way to the end of the matched string in most cases (small bug had it falling 1-4 chars behind sometimes)
* Fix bug with exporting font/binary details to SVGs
* `--chardet-cutoff` option lets you control the the cutoff for adding untested encodings to the output based on what `chardet.detect()` thinks is the right encoding
* `--suppress-chardet` command line option removes the chardet tables that are (mostly) duplicative of the decoded text tables
* Use the shortest common abbreviations for unprintable ascii
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
