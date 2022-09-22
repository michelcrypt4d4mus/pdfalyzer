# Next Release

# 1.2.0
* Dramatic expansion in the `pdfalyzer`'s binary data scouring capabilities:
   * Add `chardet` library guesses as to the encoding of all unknown byte sequences and ranks them from most to least likely
   * Add attempted decodes of all backtick, frontslash, single, double, and guillemet quoted strings in font binaries
   * Add decode attempts with `Windows-1252`, `UTF-7`, and `UTF-16` encodings
   * Add `--suppress-decodes` to suppress attempted decodes of quoted strings in font binaries
   * Cool art gets generated when you swarm a binaries quoted strings, which are mostly but not totally random
* The `--font` option takes an optional argument to limit the output to a single font ID

* Add `--limit-decodes` to suppress attempted decodes of quoted strings in font binaries over a certain length
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
