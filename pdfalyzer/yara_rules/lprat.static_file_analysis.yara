// https://github.com/lprat/static_file_analysis/blob/65089feeb3e1f4c96607a34a5301d68e61002a5e/yara_rules1/pdf.yar#L1
rule blackhole2_pdf : EK PDF
{
meta:
   author = "Josh Berry"
   date = "2016-06-27"
   description = "BlackHole2 Exploit Kit Detection"
   hash0 = "d1e2ff36a6c882b289d3b736d915a6cc"
   sample_filetype = "pdf"
   yaragenerator = "https://github.com/Xen0ph0n/YaraGenerator"
   weight = 6
   tag = "attack.initial"
strings:
   $string0 = "/StructTreeRoot 5 0 R/Type/Catalog>>"
   $string1 = "0000036095 00000 n"
   $string2 = "http://www.xfa.org/schema/xfa-locale-set/2.1/"
   $string3 = "subform[0].ImageField1[0])/Subtype/Widget/TU(Image Field)/Parent 22 0 R/F 4/P 8 0 R/T<FEFF0049006D00"
   $string4 = "0000000026 65535 f"
   $string5 = "0000029039 00000 n"
   $string6 = "0000029693 00000 n"
   $string7 = "%PDF-1.6"
   $string8 = "27 0 obj<</Subtype/Type0/DescendantFonts 28 0 R/BaseFont/KLGNYZ"
   $string9 = "0000034423 00000 n"
   $string10 = "0000000010 65535 f"
   $string11 = ">stream"
   $string12 = "/Pages 2 0 R%/StructTreeRoot 5 0 R/Type/Catalog>>"
   $string13 = "19 0 obj<</Subtype/Type1C/Length 23094/Filter/FlateDecode>>stream"
   $string14 = "0000003653 00000 n"
   $string15 = "0000000023 65535 f"
   $string16 = "0000028250 00000 n"
   $string17 = "iceRGB>>>>/XStep 9.0/Type/Pattern/TilingType 2/YStep 9.0/BBox[0 0 9 9]>>stream"
   $string18 = "<</Root 1 0 R>>"
condition:
   18 of them
}

rule bleedinglife2_adobe_2010_2884_exploit : EK
{
meta:
   author = "Josh Berry"
   date = "2016-06-26"
   description = "BleedingLife2 Exploit Kit ADOBE"
   hash0 = "b22ac6bea520181947e7855cd317c9ac"
   sample_filetype = "unknown"
   yaragenerator = "https://github.com/Xen0ph0n/YaraGenerator"
   weight = 6
   tag = "attack.initial"
strings:
   $string0 = "_autoRepeat"
   $string1 = "embedFonts"
   $string2 = "KeyboardEvent"
   $string3 = "instanceStyles"
   $string4 = "InvalidationType"
   $string5 = "autoRepeat"
   $string6 = "getScaleX"
   $string7 = "RadioButton_selectedDownIcon"
   $string8 = "configUI"
   $string9 = "deactivate"
   $string10 = "fl.controls:Button"
   $string11 = "_mouseStateLocked"
   $string12 = "fl.core.ComponentShim"
   $string13 = "toString"
   $string14 = "_group"
   $string15 = "addRadioButton"
   $string16 = "inCallLaterPhase"
   $string17 = "oldMouseState"
condition:
   17 of them
}

rule bleedinglife2_adobe_2010_1297_exploit : EK PDF
{
meta:
   author = "Josh Berry"
   date = "2016-06-26"
   description = "BleedingLife2 Exploit Kit PDF"
   hash0 = "8179a7f91965731daa16722bd95f0fcf"
   sample_filetype = "unknown"
   yaragenerator = "https://github.com/Xen0ph0n/YaraGenerator"
   weight = 6
   tag = "attack.initial"
strings:
   $string0 = "getSharedStyle"
   $string1 = "currentCount"
   $string2 = "String"
   $string3 = "setSelection"
   $string4 = "BOTTOM"
   $string5 = "classToInstancesDict"
   $string6 = "buttonDown"
   $string7 = "focusRect"
   $string8 = "pill11"
   $string9 = "TEXT_INPUT"
   $string10 = "restrict"
   $string11 = "defaultButtonEnabled"
   $string12 = "copyStylesToChild"
   $string13 = " xmlns:xmpMM"
   $string14 = "_editable"
   $string15 = "classToDefaultStylesDict"
   $string16 = "IMEConversionMode"
   $string17 = "Scene 1"
condition:
   17 of them
}

rule phoenix_pdf : EK PDF
{
meta:
   author = "Josh Berry"
   date = "2016-06-26"
   description = "Phoenix Exploit Kit PDF"
   hash0 = "16de68e66cab08d642a669bf377368da"
   hash1 = "bab281fe0cf3a16a396550b15d9167d5"
   sample_filetype = "pdf"
   yaragenerator = "https://github.com/Xen0ph0n/YaraGenerator"
   weight = 6
   tag = "attack.initial"
strings:
   $string0 = "0000000254 00000 n"
   $string1 = "0000000295 00000 n"
   $string2 = "trailer<</Root 1 0 R /Size 7>>"
   $string3 = "0000000000 65535 f"
   $string4 = "3 0 obj<</JavaScript 5 0 R >>endobj"
   $string5 = "0000000120 00000 n"
   $string6 = "%PDF-1.0"
   $string7 = "startxref"
   $string8 = "0000000068 00000 n"
   $string9 = "endobjxref"
   $string10 = ")6 0 R ]>>endobj"
   $string11 = "0000000010 00000 n"
condition:
   11 of them
}

rule phoenix_pdf2 : EK PDF
{
meta:
   author = "Josh Berry"
   date = "2016-06-26"
   description = "Phoenix Exploit Kit PDF"
   hash0 = "33cb6c67f58609aa853e80f718ab106a"
   sample_filetype = "pdf"
   yaragenerator = "https://github.com/Xen0ph0n/YaraGenerator"
   weight = 6
   tag = "attack.initial"
strings:
   $string0 = "\\nQb<%"
   $string1 = "0000000254 00000 n"
   $string2 = ":S3>v0$EF"
   $string3 = "trailer<</Root 1 0 R /Size 7>>"
   $string4 = "%PDF-1.0"
   $string5 = "0000000000 65535 f"
   $string6 = "endstream"
   $string7 = "0000000010 00000 n"
   $string8 = "6 0 obj<</JS 7 0 R/S/JavaScript>>endobj"
   $string9 = "3 0 obj<</JavaScript 5 0 R >>endobj"
   $string10 = "}pr2IE"
   $string11 = "0000000157 00000 n"
   $string12 = "1 0 obj<</Type/Catalog/Pages 2 0 R /Names 3 0 R >>endobj"
   $string13 = "5 0 obj<</Names[("
condition:
   13 of them
}

rule phoenix_pdf3 : EK PDF
{
meta:
   author = "Josh Berry"
   date = "2016-06-26"
   description = "Phoenix Exploit Kit PDF"
   hash0 = "bab281fe0cf3a16a396550b15d9167d5"
   sample_filetype = "pdf"
   yaragenerator = "https://github.com/Xen0ph0n/YaraGenerator"
   weight = 6
   tag = "attack.initial"
strings:
   $string0 = "trailer<</Root 1 0 R /Size 7>>"
   $string1 = "stream"
   $string2 = ";_oI5z"
   $string3 = "0000000010 00000 n"
   $string4 = "3 0 obj<</JavaScript 5 0 R >>endobj"
   $string5 = "7 0 obj<</Filter[ /FlateDecode /ASCIIHexDecode /ASCII85Decode ]/Length 3324>>"
   $string6 = "endobjxref"
   $string7 = "L%}gE("
   $string8 = "0000000157 00000 n"
   $string9 = "1 0 obj<</Type/Catalog/Pages 2 0 R /Names 3 0 R >>endobj"
   $string10 = "0000000120 00000 n"
   $string11 = "4 0 obj<</Type/Page/Parent 2 0 R /Contents 12 0 R>>endobj"
condition:
   11 of them
}

// rule OpenAction_In_PDF {
//    meta:
//       description = "Detects OpenAction in PDF"
//       author = "Lionel PRAT"
//       reference = "Basic rule PDF"
//       version = "0.1"
//       weight = 1
//       var_match = "pdf_oaction_bool"
//    strings:
//       $a = /\/AA|\/OpenAction/
//    condition:
//       (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/) and $a
// }

// rule Action_In_PDF {
//    meta:
//       description = "Detects Action in PDF"
//       author = "Lionel PRAT"
//       reference = "Basic rule PDF"
//       version = "0.1"
//       weight = 1
//       var_match = "pdf_action_bool"
//    strings:
//       $a = /\/Action/
//    condition:
//       (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/) and $a
// }

// rule Javascript_In_PDF {
//    meta:
//       description = "Detects Javascript in PDF"
//       author = "Lionel PRAT"
//       reference = "Basic rule PDF"
//       version = "0.1"
//       weight = 1
//       var_match = "pdf_javascript_bool"
//    strings:
//       $a = /\/JavaScript |\/JS /
//    condition:
//       (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/) and ($a or PDFStats_JavascriptObjects matches /[0-9]+/)
// }

// rule Encrypted_In_PDF {
//    meta:
//       description = "Detects part Encrypted in PDF"
//       author = "Lionel PRAT"
//       reference = "PDF encrypted"
//       version = "0.1"
//       weight = 6
//    condition:
//       (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/) and PDFStats_Encrypted_bool
// }

// rule ASCIIDecode_In_PDF {
//    meta:
//       description = "Detects ASCII Decode in PDF"
//       author = "Lionel PRAT"
//       reference = "Basic rule PDF"
//       version = "0.1"
//       weight = 1
//       var_match = "pdf_asciidecode_bool"
//    strings:
//       $a = /\/ASCIIHexDecode|\/ASCII85Decode/
//    condition:
//       (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/) and $a
// }

// rule oldversion_In_PDF {
//    meta:
//       description = "Old version PDF"
//       author = "Lionel PRAT"
//       reference = "Basic rule PDF"
//       version = "0.1"
//       weight = 0
//       var_match = "pdf_oldver12_bool"
//    strings:
//       $ver = /%PDF-1\.[3-9]/
//    condition:
//       (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/) and not $ver
// }

// rule js_wrong_version_PDF {
// 	meta:
// 		author = "Glenn Edwards (@hiddenillusion)"
// 		description = "JavaScript was introduced in v1.3"
// 		ref = "http://wwwimages.adobe.com/www.adobe.com/content/dam/Adobe/en/devnet/pdf/pdfs/pdf_reference_1-7.pdf"
// 		version = "0.1"
// 		weight = 2

//         strings:
//                 $magic = { 25 50 44 46 }
// 				$js = /\/JavaScript/
// 				$ver = /%PDF-1\.[3-9]/

//         condition:
//                 ($magic at 0 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/) and $js and (not $ver or pdf_oldver12_bool)
// }

// rule embed_wrong_version_PDF {
// 	meta:
// 		author = "Glenn Edwards (@hiddenillusion)"
// 		description = "EmbeddedFiles were introduced in v1.3"
// 		ref = "http://wwwimages.adobe.com/www.adobe.com/content/dam/Adobe/en/devnet/pdf/pdfs/pdf_reference_1-7.pdf"
// 		version = "0.1"
// 		weight = 2
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
//         strings:
//                 $magic = { 25 50 44 46 }
// 				$embed = /\/EmbeddedFiles/
// 				$ver = /%PDF-1\.[3-9]/

//         condition:
//                 ($magic at 0 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) and $embed and (not $ver or pdf_oldver12_bool)
// }

// rule XDP_In_PDF {
//    meta:
//       description = "file XDP in PDF"
//       author = "Lionel PRAT"
//       reference = "Basic rule PDF"
//       version = "0.1"
//       weight = 2
//       var_match = "pdf_xdp_bool"
//       tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
//    condition:
//       (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) and FileType matches /CL_TYPE_XDP/
// }

// rule suspicious_js_PDF {
// 	meta:
// 		author = "Glenn Edwards (@hiddenillusion) - modified by Lionel PRAT"
// 		version = "0.1"
// 		description = "Suspicious JS in PDF metadata"
// 		weight = 5
// 		check_level2 = "check_js_bool"
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
// 	strings:
// 		$magic = { 25 50 44 46 }

// 		$attrib0 = /\/OpenAction|\/AA/
// 		$attrib1 = /\/JavaScript |\/JS /

// 		$js0 = "eval"
// 		$js1 = "Array"
// 		$js2 = "String.fromCharCode"
// 		$js3 = /(^|\n)[a-zA-Z_$][0-9a-zA-Z_$]{0,100}=[^;]{200,}/

// 	condition:
// 		($magic in (0..1024) or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) and ((all of ($attrib*)) or (pdf_oaction_bool and pdf_javascript_bool)) and 2 of ($js*)
// }

// rule invalide_structure_PDF {
// 	meta:
// 		author = "Glenn Edwards (@hiddenillusion)"
// 		version = "0.1"
// 		description = "Invalide structure PDF"
// 		weight = 5
// 		var_match = "pdf_invalid_struct_bool"
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
//         strings:
//                 $magic = { 25 50 44 46 }
// 				// Required for a valid PDF
//                 $reg0 = /trailer\r?\n?.*\/Size.*\r?\n?\.*/
//                 $reg1 = /\/Root.*\r?\n?.*startxref\r?\n?.*\r?\n?%%EOF/
//         condition:
//                 $magic in (0..1024) and not $reg0 and not $reg1
// }

// rule clam_invalide_structure_PDF {
// 	meta:
// 		author = "Lionel PRAT"
// 		description = "clamav check Invalide structure PDF"
// 		weight = 5
// 		version = "0.1"
// 		var_match = "pdf_invalid_struct_bool"
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
//         condition:
//                 (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) and (PDFStats_NoXREF_bool or PDFStats_BadTrailer_bool or PDFStats_NoEOF_bool or PDFStats_BadVersion_bool or PDFStats_BadHeaderPosition_bool)
// }

// rule XFA_exploit_in_PDF {
//    meta:
//       description = "PDF potential exploit XFA CVE-2010-0188"
//       author = "Lionel PRAT"
//       reference = "https://www.exploit-db.com/exploits/11787"
//       version = "0.1"
//       weight = 6
//       tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
//       check_level2 = "check_command_bool"
//    strings:
//       $nop = "kJCQkJCQkJCQkJCQ"
//       $xfa = /\/XFA|http:\/\/www\.xfa\.org\/schema\//
//       $tif = "tif"
//       $img = "ImageField"
//    condition:
//       (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) and $xfa and $img and $tif and $nop
// }

// rule XFA_withJS_in_PDF {
//    meta:
//       description = "Detects Potential XFA with JS in PDF"
//       author = "Lionel PRAT"
//       reference = "EK Blackhole PDF exploit"
//       version = "0.1"
//       weight = 4
//       var_match = "pdf_xfajs_bool"
//       tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
//       check_level2 = "check_command_bool"
//    strings:
//       $a = /\/XFA|http:\/\/www\.xfa\.org\/schema\//
//       $b = "x-javascript" nocase
//    condition:
//       (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) and $a and ($b or pdf_javascript_bool or pdf_oaction_bool)
// }

// rule XFA_in_PDF {
//    meta:
//       description = "Detects Potential XFA with JS in PDF"
//       author = "Lionel PRAT"
//       reference = "EK Blackhole PDF exploit"
//       version = "0.1"
//       weight = 3
//       var_match = "pdf_xfa_bool"
//       tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
//       check_level2 = "check_command_bool"
//    strings:
//       $a = /\/XFA|http:\/\/www\.xfa\.org\/schema\//
//    condition:
//       (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) and $a
// }

// rule URI_on_OPENACTION_in_PDF {
//    meta:
//       description = "Detects Potential URI on OPENACTION in PDF"
//       author = "Lionel PRAT"
//       reference = "TokenCanary.pdf"
//       version = "0.1"
//       weight = 2
//       var_match = "pdf_uri_bool"
//       tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
//    strings:
//       $a = /\/S\s*\/URI\s*\/URI\s*\(/
//       $b = /\OpenAction/
//    condition:
//       (uint32(0) == 0x46445025 or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) and $a and ($b or pdf_oaction_bool)
// }

rule shellcode_metadata_PDF {
        meta:
                author = "Glenn Edwards (@hiddenillusion)"
                version = "0.1"
                description = "Potential shellcode in PDF metadata"
                weight = 5
                tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
                check_level2 = "check_command_bool"
        strings:
                $magic = { 25 50 44 46 }

                $reg_keyword = /\/Keywords.?\(([a-zA-Z0-9]{200,})/ //~6k was observed in BHEHv2 PDF exploits holding the shellcode
                $reg_author = /\/Author.?\(([a-zA-Z0-9]{200,})/
                $reg_title = /\/Title.?\(([a-zA-Z0-9]{200,})/
                $reg_producer = /\/Producer.?\(([a-zA-Z0-9]{200,})/
                $reg_creator = /\/Creator.?\(([a-zA-Z0-9]{300,})/
                $reg_create = /\/CreationDate.?\(([a-zA-Z0-9]{200,})/

        condition:
                $magic in (0..1024) and 1 of ($reg*)
}

// rule potential_exploit_PDF{
// 	meta:
// 		author = "Glenn Edwards (@hiddenillusion) - modified by Lionel PRAT"
// 		version = "0.1"
// 		weight = 5
// 		description = "Potential exploit in PDF metadata"
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
// 		check_level2 = "check_command_bool"
// 	strings:
// 		$magic = { 25 50 44 46 }

// 		$attrib0 = /\/JavaScript |\/JS /
// 		$attrib3 = /\/ASCIIHexDecode/
// 		$attrib4 = /\/ASCII85Decode/

// 		$action0 = /\/Action/
// 		$action1 = "Array"
// 		$shell = "A"
// 		$cond0 = "unescape"
// 		$cond1 = "String.fromCharCode"

// 		$nop = "%u9090%u9090"
// 	condition:
// 		($magic in (0..1024) or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) and ((2 of ($attrib*)) or (pdf_asciidecode_bool and pdf_javascript_bool)) or (($action0 or pdf_action_bool) and #shell > 10 and 1 of ($cond*)) or (($action1 or pdf_action_bool) and $cond0 and $nop)
// }

// //TODO: complete list
// //     .application$|.chm$|.appref-ms$|.cmdline$|.jnlp$|.exe$|.gadget$|.dll$|.lnk$|.pif$|.com$|.sfx$|.bat$|.cmd$|.scr$|.sys$|.hta$|.cpl$|.msc$|.inf$|.scf$|.reg$|.jar$|.vb\.*$|.js\.*$|.ws\.+$|.ps\w+$|.ms\w+$|.jar$|.url$
// //     .rtf$|\.ppt\.*$|.xls\.*$|.doc\.*$|.pdf$|.zip$|.rar$|.tmp$|.py\.*$|.dotm$|.xltm$|.xlam$|.potm$|.ppam$|.ppsm$|.sldm$

// rule dangerous_embed_file_PDF{
// 	meta:
// 		author = "Lionel PRAT"
// 		version = "0.1"
// 		weight = 8
// 		description = "Dangerous embed file in PDF"
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
// 	condition:
// 		FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ and FileType matches /CL_TYPE_MSEXE|CL_TYPE_MS-EXE|CL_TYPE_MS-DLL|CL_TYPE_ELF|CL_TYPE_MACHO|CL_TYPE_OLE2|CL_TYPE_MSOLE2|CL_TYPE_MSCAB|CL_TYPE_RTF|CL_TYPE_ZIP|CL_TYPE_OOXML|CL_TYPE_AUTOIT|CL_TYPE_JAVA|CL_TYPE_SWF/
// }

// rule suspect_embed_file_PDF{
// 	meta:
// 		author = "Lionel PRAT"
// 		version = "0.1"
// 		weight = 4
// 		description = "suspect embed file in PDF"
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
// 	condition:
// 		FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ and not FileType matches /CL_TYPE_TEXT|CL_TYPE_BINARY_DATA|CL_TYPE_UNKNOWN|CL_TYPE_ASCII|CL_TYPE_UTF/
// }

// rule PDF_fileexport {
// 	meta:
// 		author = "Lionel PRAT"
// 		version = "0.1"
// 		weight = 5
// 		description = "PDF fonction export file (check file for found name)"
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
// 	strings:
// 		$export = "exportDataObject" nocase wide ascii
// 		$cname = "cname" nocase wide ascii
// 	condition:
// 		(((uint32(0) == 0x74725c7b and uint16(4) == 0x3166) or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) or FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/) and $export and $cname
// }

// rule embed_file_PDF{
// 	meta:
// 		author = "Lionel PRAT"
// 		version = "0.1"
// 		weight = 0
// 		description = "unknown embed file in PDF"
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
// 		check_level2 = "check_entropy_bool"
// 	condition:
// 		FileParentType matches /->CL_TYPE_PDF$|CL_TYPE_PDF_document$/ and FileType matches /CL_TYPE_TEXT|CL_TYPE_BINARY_DATA|CL_TYPE_UNKNOWN|CL_TYPE_ASCII|CL_TYPE_UTF/
// }

// rule PDFFile_date{
// 	meta:
// 		author = "Lionel PRAT"
// 		version = "0.1"
// 		weight = 3
// 		description = "PDF File with same CreationDate and ModificationDate"
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
// 	condition:
// 		((uint32(0) == 0x74725c7b and uint16(4) == 0x3166) or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) and PDFStats_CreationDate == PDFStats_ModificationDate and PDFStats_CreationDate matches /[0-9]+/
// }

// rule PDFFile_1page{
// 	meta:
// 		author = "Lionel PRAT"
// 		version = "0.1"
// 		weight = 2
// 		description = "PDF File with only 1 page"
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
// 	condition:
// 		((uint32(0) == 0x74725c7b and uint16(4) == 0x3166) or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i) and PDFStats_PageCount_int == 1
// }

// // rule PDFFile{
// 	meta:
// 		author = "Lionel PRAT"
// 		version = "0.1"
// 		weight = 1
// 		description = "PDF File"
// 		tag = "attack.initial_access,attack.t1189,attack.t1192,attack.t1193,attack.t1194,attack.execution"
// 		var_match = "pdf_file_bool"
// 	condition:
// 		(uint32(0) == 0x74725c7b and uint16(4) == 0x3166) or FileType matches /CL_TYPE_PDF/ or PathFile matches /.*\.pdf$/i or CDBNAME matches /.*\.pdf$/i
// }
