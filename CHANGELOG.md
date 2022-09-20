# Next Release

# 1.0.1
* Fix issue with directly embedded `/Resources` not being walked correctly (along with their fonts)
* Introduce `PdfObjectRef` tuple to contain the root reference key, the actual reference address str, and the referenced obj
* Add warnings if any PDF objects are missing from the tree

# 1.0.0
* Initial release
* Change command line option style (capital letters for debugging, 3 letter codes for export)
* No need to explicitly call `walk_pdf()`
* Fix parent/child relationships for `/StructElem`
