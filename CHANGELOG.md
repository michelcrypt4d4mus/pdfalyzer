# Next Release
* Add `/Dest` to `NON_TREE_REFERENCES`
* Fix printing of suspicious font bytes when suspicions are near start or end of stream
* Only print font bytes that failed to decode if there are actually any such bytes

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
