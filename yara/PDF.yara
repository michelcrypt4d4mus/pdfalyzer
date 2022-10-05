import "math"


rule Cobaltgang_PDF_Metadata_Rev_A {
   meta:
        description = "Find documents saved from the same potential Cobalt Gang PDF template"
        author = "Palo Alto Networks Unit 42"
        date = "2018-10-25"
        reference = "https://researchcenter.paloaltonetworks.com/2018/10/unit42-new-techniques-uncover-attribute-cobalt-gang-commodity-builders-infrastructure-revealed/"
   strings:
        $ = "<xmpMM:DocumentID>uuid:31ac3688-619c-4fd4-8e3f-e59d0354a338" ascii wide
   condition:
        any of them
}


rule PDF_Embedded_Exe : PDF
{
	meta:
		ref = "https://github.com/jacobsoo/Yara-Rules/blob/master/PDF_Embedded_Exe.yar"
	strings:
    	$header = {25 50 44 46}
    	$Launch_Action = {3C 3C 2F 53 2F 4C 61 75 6E 63 68 2F 54 79 70 65 2F 41 63 74 69 6F 6E 2F 57 69 6E 3C 3C 2F 46}
        $exe = {3C 3C 2F 45 6D 62 65 64 64 65 64 46 69 6C 65 73}
    condition:
    	$header at 0 and $Launch_Action and $exe
}


rule SUSP_Bad_PDF {
   meta:
        description = "Detects PDF that embeds code to steal NTLM hashes"
        author = "Florian Roth, Markus Neis"
        reference = "Internal Research"
        date = "2018-05-03"
        hash1 = "d8c502da8a2b8d1c67cb5d61428f273e989424f319cfe805541304bdb7b921a8"
   strings:
        $s1 = "         /F (http//" ascii
        $s2 = "        /F (\\\\\\\\" ascii
        $s3 = "<</F (\\\\" ascii
   condition:
        ( uint32(0) == 0x46445025 or uint32(0) == 0x4450250a ) and 1 of them
}


rule malicious_author : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 5
	strings:
		$magic = { 25 50 44 46 }
		$reg0 = /Creator.?\(yen vaw\)/
		$reg1 = /Title.?\(who cis\)/
		$reg2 = /Author.?\(ser pes\)/
	condition:
		$magic at 0 and all of ($reg*)
}


rule suspicious_version : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 3
	strings:
		$magic = { 25 50 44 46 }
		$ver = /%PDF-1.\d{1}/
	condition:
		$magic at 0 and not $ver
}


rule suspicious_creation : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 2
	strings:
		$magic = { 25 50 44 46 }
		$header = /%PDF-1\.(3|4|6)/
		$create0 = /CreationDate \(D:20101015142358\)/
		$create1 = /CreationDate \(2008312053854\)/
	condition:
		$magic at 0 and $header and 1 of ($create*)
}


rule suspicious_title : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 4

	strings:
		$magic = { 25 50 44 46 }
		$header = /%PDF-1\.(3|4|6)/

		$title0 = "who cis"
		$title1 = "P66N7FF"
		$title2 = "Fohcirya"
	condition:
		$magic at 0 and $header and 1 of ($title*)
}


rule suspicious_author : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 4
	strings:
		$magic = { 25 50 44 46 }
		$header = /%PDF-1\.(3|4|6)/
		$author0 = "Ubzg1QUbzuzgUbRjvcUb14RjUb1"
		$author1 = "ser pes"
		$author2 = "Miekiemoes"
		$author3 = "Nsarkolke"
	condition:
		$magic at 0 and $header and 1 of ($author*)
}


rule suspicious_producer : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 2

	strings:
		$magic = { 25 50 44 46 }
		$header = /%PDF-1\.(3|4|6)/

		$producer0 = /Producer \(Scribus PDF Library/
		$producer1 = "Notepad"
	condition:
		$magic at 0 and $header and 1 of ($producer*)
}


rule suspicious_creator : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 3

	strings:
		$magic = { 25 50 44 46 }
		$header = /%PDF-1\.(3|4|6)/

		$creator0 = "yen vaw"
		$creator1 = "Scribus"
		$creator2 = "Viraciregavi"
	condition:
		$magic at 0 and $header and 1 of ($creator*)
}


rule possible_exploit : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 3

	strings:
		$magic = { 25 50 44 46 }

		$attrib0 = /\/JavaScript /
		$attrib3 = /\/ASCIIHexDecode/
		$attrib4 = /\/ASCII85Decode/

		$action0 = /\/Action/
		$action1 = "Array"
		$shell = "A"
		$cond0 = "unescape"
		$cond1 = "String.fromCharCode"

		$nop = "%u9090%u9090"
	condition:
		$magic at 0 and (2 of ($attrib*)) or ($action0 and #shell > 10 and 1 of ($cond*)) or ($action1 and $cond0 and $nop)
}


rule shellcode_blob_metadata : PDF
{
    meta:
        author = "Glenn Edwards (@hiddenillusion)"
        version = "0.1"
        description = "When there's a large Base64 blob inserted into metadata fields it often indicates shellcode to later be decoded"
        weight = 4
    strings:
        $magic = { 25 50 44 46 }
        $reg_keyword = /\/Keywords.?\(([a-zA-Z0-9]{200,})/ //~6k was observed in BHEHv2 PDF exploits holding the shellcode
        $reg_author = /\/Author.?\(([a-zA-Z0-9]{200,})/
        $reg_title = /\/Title.?\(([a-zA-Z0-9]{200,})/
        $reg_producer = /\/Producer.?\(([a-zA-Z0-9]{200,})/
        $reg_creator = /\/Creator.?\(([a-zA-Z0-9]{300,})/
        $reg_create = /\/CreationDate.?\(([a-zA-Z0-9]{200,})/
    condition:
        $magic at 0 and 1 of ($reg*)
}

rule multiple_filtering : PDF
{
    meta:
        author = "Glenn Edwards (@hiddenillusion)"
        version = "0.2"
        weight = 3
    strings:
        $magic = { 25 50 44 46 }
        $attrib = /\/Filter.*?(\/ASCIIHexDecode\W+?|\/LZWDecode\W+?|\/ASCII85Decode\W+?|\/FlateDecode\W+?|\/RunLengthDecode){2}?/
        // left out: /CCITTFaxDecode, JBIG2Decode, DCTDecode, JPXDecode, Crypt
    condition:
        $magic at 0 and $attrib
}

rule suspicious_js : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 3

	strings:
		$magic = { 25 50 44 46 }
		$attrib0 = /\/OpenAction /
		$attrib1 = /\/JavaScript /
		$js0 = "eval"
		$js1 = "Array"
		$js2 = "String.fromCharCode"
	condition:
		$magic at 0 and all of ($attrib*) and 2 of ($js*)
}


rule suspicious_launch_action : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 2
	strings:
		$magic = { 25 50 44 46 }
		$attrib0 = /\/Launch/
		$attrib1 = /\/URL /
		$attrib2 = /\/Action/
		$attrib3 = /\/F /
	condition:
		$magic at 0 and 3 of ($attrib*)
}


rule suspicious_embed : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		ref = "https://feliam.wordpress.com/2010/01/13/generic-pdf-exploit-hider-embedpdf-py-and-goodbye-av-detection-012010/"
		weight = 2

	strings:
		$magic = { 25 50 44 46 }

		$meth0 = /\/Launch/
		$meth1 = /\/GoTo(E|R)/ //means go to embedded or remote
		$attrib0 = /\/URL /
		$attrib1 = /\/Action/
		$attrib2 = /\/Filespec/

	condition:
		$magic at 0 and 1 of ($meth*) and 2 of ($attrib*)
}


rule suspicious_obfuscation : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 2

	strings:
		$magic = { 25 50 44 46 }
		$reg = /\/\w#[a-zA-Z0-9]{2}#[a-zA-Z0-9]{2}/

	condition:
		$magic at 0 and #reg > 5
}


rule invalid_XObject_js : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		description = "XObject's require v1.4+"
		ref = "https://blogs.adobe.com/ReferenceXObjects/"
		version = "0.1"
		weight = 2

	strings:
		$magic = { 25 50 44 46 }
		$ver = /%PDF-1\.[4-9]/

		$attrib0 = /\/XObject/
		$attrib1 = /\/JavaScript/

	condition:
		$magic at 0 and not $ver and all of ($attrib*)
}


rule invalid_trailer_structure : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		weight = 1

    strings:
        $magic = { 25 50 44 46 }
        // Required for a valid PDF
        $reg0 = /trailer\r?\n?.*\/Size.*\r?\n?\.*/
        $reg1 = /\/Root.*\r?\n?.*startxref\r?\n?.*\r?\n?%%EOF/
    condition:
        $magic at 0 and not $reg0 and not $reg1
}


rule multiple_versions : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
        description = "Written very generically and doesn't hold any weight - just something that might be useful to know about to help show incremental updates to the file being analyzed"
		weight = 0
    strings:
        $magic = { 25 50 44 46 }
        $trailer = "trailer"
        $eof = "%%EOF"
    condition:
        $magic at 0 and #trailer > 1 and #eof > 1
}


rule js_wrong_version : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		description = "JavaScript was introduced in v1.3"
		ref = "http://wwwimages.adobe.com/www.adobe.com/content/dam/Adobe/en/devnet/pdf/pdfs/pdf_reference_1-7.pdf"
		version = "0.1"
		weight = 2

    strings:
        $magic = { 25 50 44 46 }
        $js = /\/JavaScript/
        $ver = /%PDF-1\.[3-9]/

    condition:
        $magic at 0 and $js and not $ver
}


rule JBIG2_wrong_version : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		description = "JBIG2 was introduced in v1.4"
		ref = "http://wwwimages.adobe.com/www.adobe.com/content/dam/Adobe/en/devnet/pdf/pdfs/pdf_reference_1-7.pdf"
		version = "0.1"
		weight = 1

    strings:
        $magic = { 25 50 44 46 }
        $js = /\/JBIG2Decode/
        $ver = /%PDF-1\.[4-9]/

    condition:
        $magic at 0 and $js and not $ver
}


rule FlateDecode_wrong_version : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		description = "Flate was introduced in v1.2"
		ref = "http://wwwimages.adobe.com/www.adobe.com/content/dam/Adobe/en/devnet/pdf/pdfs/pdf_reference_1-7.pdf"
		version = "0.1"
		weight = 1
    strings:
        $magic = { 25 50 44 46 }
        $js = /\/FlateDecode/
        $ver = /%PDF-1\.[2-9]/
    condition:
        $magic at 0 and $js and not $ver
}


rule embed_wrong_version : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		description = "EmbeddedFiles were introduced in v1.3"
		ref = "http://wwwimages.adobe.com/www.adobe.com/content/dam/Adobe/en/devnet/pdf/pdfs/pdf_reference_1-7.pdf"
		version = "0.1"
		weight = 1
    strings:
        $magic = { 25 50 44 46 }
        $embed = /\/EmbeddedFiles/
        $ver = /%PDF-1\.[3-9]/
    condition:
        $magic at 0 and $embed and not $ver
}


rule invalid_xref_numbers : PDF
{
    meta:
        author = "Glenn Edwards (@hiddenillusion)"
        version = "0.1"
        description = "The first entry in a cross-reference table is always free and has a generation number of 65,535"
        notes = "This can be also be in a stream..."
        weight = 1
    strings:
        $magic = { 25 50 44 46 }
        $reg0 = /xref\r?\n?.*\r?\n?.*65535\sf/
        $reg1 = /endstream.*?\r??\n??endobj.*?\r??\n??startxref/
    condition:
        $magic at 0 and not $reg0 and not $reg1
}


rule js_splitting : PDF
{
    meta:
        author = "Glenn Edwards (@hiddenillusion)"
        version = "0.1"
        description = "These are commonly used to split up JS code"
        weight = 2
    strings:
        $magic = { 25 50 44 46 }
        $js = /\/JavaScript/
        $s0 = "getAnnots"
        $s1 = "getPageNumWords"
        $s2 = "getPageNthWord"
        $s3 = "this.info"
    condition:
        $magic at 0 and $js and 1 of ($s*)
}


rule header_evasion : PDF
{
    meta:
            author = "Glenn Edwards (@hiddenillusion)"
            description = "3.4.1, 'File Header' of Appendix H states that ' Acrobat viewers require only that the header appear somewhere within the first 1024 bytes of the file.'  Therefore, if you see this trigger then any other rule looking to match the magic at 0 won't be applicable"
            ref = "http://wwwimages.adobe.com/www.adobe.com/content/dam/Adobe/en/devnet/pdf/pdfs/pdf_reference_1-7.pdf"
            version = "0.1"
            weight = 3

    strings:
            $magic = { 25 50 44 46 }
    condition:
            $magic in (5..1024) and #magic == 1
}


rule BlackHole_v2 : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		ref = "http://fortknoxnetworks.blogspot.no/2012/10/blackhhole-exploit-kit-v-20-url-pattern.html"
		weight = 3

	strings:
		$magic = { 25 50 44 46 }
		$content = "Index[5 1 7 1 9 4 23 4 50"

	condition:
		$magic at 0 and $content
}


rule XDP_embedded_PDF : PDF
{
	meta:
		author = "Glenn Edwards (@hiddenillusion)"
		version = "0.1"
		ref = "http://blog.9bplus.com/av-bypass-for-malicious-pdfs-using-xdp"
        weight = 1

	strings:
		$s1 = "<pdf xmlns="
		$s2 = "<chunk>"
		$s3 = "</pdf>"
		$header0 = "%PDF"
		$header1 = "JVBERi0"

	condition:
		all of ($s*) and 1 of ($header*)
}

// rule pdfjs_hunter
// {
//     strings:
//         $pdf_header = "%PDF"
//     condition:
//         new_file and
//         (
//             file_type contains "pdf" or
//             $pdf_header in (0..1024)
//         )
//         and tags contains "js-embedded"
// }


rule PDF_Document_with_Embedded_IQY_File
{
    meta:
        Author = "InQuest Labs"
        Description = "This signature detects IQY files embedded within PDF documents which use a JavaScript OpenAction object to run the IQY."
        Reference = "https://blog.inquest.net"

    strings:
        $pdf_magic = "%PDF"
        $efile = /<<\/JavaScript [^\x3e]+\/EmbeddedFile/
        $fspec = /<<\/Type\/Filespec\/F\(\w+\.iqy\)\/UF\(\w+\.iqy\)/
        $openaction = /OpenAction<<\/S\/JavaScript\/JS\(/

        /*
          <</Type/Filespec/F(10082016.iqy)/UF(10082016.iqy)/EF<</F 1 0 R/UF 1 0 R>>/Desc(10082016.iqy)>>
          ...
          <</Names[(10082016.iqy) 2 0 R]>>
          ...
          <</JavaScript 9 0 R/EmbeddedFiles 10 0 R>>
          ...
          OpenAction<</S/JavaScript/JS(
        */

        /*
            obj 1.9
             Type: /EmbeddedFile
             Referencing:
             Contains stream
              <<
                /Length 51
                /Type /EmbeddedFile
                /Filter /FlateDecode
                /Params
                  <<
                    /ModDate "(D:20180810145018+03'00')"
                    /Size 45
                  >>
              >>
             WEB
            1
            http://i86h.com/data1.dat
            2
            3
            4
            5
        */

   condition:
      $pdf_magic in (0..60)  and all of them
}

// rule malpdf_hunter
// {
//     strings:
//         $pdf_header = "%PDF"
//         $encrypted  = "/Encrypt"
//     condition:
//         new_file and
//         (
//             file_type contains "pdf" or
//             $pdf_header in (0..1024)
//         )
//         and (positives > 0 or $encrypted)
// }


rule Base64_Encoded_Powershell_Directives
{
    meta:
        Author      = "InQuest Labs"
        Reference   = "https://inquest.net/blog/2019/07/19/base64-encoded-powershell-pivots"
        Samples     = "https://github.com/InQuest/malware-samples/tree/master/2019-07-Base64-Encoded-Powershell-Directives"
        Description = "This signature detects base64 encoded Powershell directives."

    strings:
        // Copy-Item
        $enc01 = /(Q\x32\x39weS\x31JdGVt[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]Db\x33B\x35LUl\x30ZW[\x30-\x33]|[\x2b\x2f-\x39A-Za-z][\x30EUk]NvcHktSXRlb[Q-Za-f])/
        // ForEach-Object
        $enc02 = /(Rm\x39yRWFjaC\x31PYmplY\x33[Q-T]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]Gb\x33JFYWNoLU\x39iamVjd[A-P]|[\x2b\x2f-\x39A-Za-z][\x30EUk]ZvckVhY\x32gtT\x32JqZWN\x30[\x2b\x2f-\x39A-Za-z])/
        // Get-ChildItem
        $enc03 = /(R\x32V\x30LUNoaWxkSXRlb[Q-Za-f]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]HZXQtQ\x32hpbGRJdGVt[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x30EUk]dldC\x31DaGlsZEl\x30ZW[\x30-\x33])/
        // Get-ItemPropertyValue
        $enc04 = /(R\x32V\x30LUl\x30ZW\x31Qcm\x39wZXJ\x30eVZhbHVl[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]HZXQtSXRlbVByb\x33BlcnR\x35VmFsdW[U-X]|[\x2b\x2f-\x39A-Za-z][\x30EUk]dldC\x31JdGVtUHJvcGVydHlWYWx\x31Z[Q-Za-f])/
        // Get-Random
        $enc05 = /(R\x32V\x30LVJhbmRvb[Q-Za-f]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]HZXQtUmFuZG\x39t[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x30EUk]dldC\x31SYW\x35kb\x32[\x30-\x33])/
        // Join-Path
        $enc06 = /(Sm\x39pbi\x31QYXRo[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]Kb\x32luLVBhdG[g-j]|[\x2b\x2f-\x39A-Za-z][\x30EUk]pvaW\x34tUGF\x30a[A-P])/
        // Move-Item
        $enc07 = /(TW\x39\x32ZS\x31JdGVt[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]Nb\x33ZlLUl\x30ZW[\x30-\x33]|[\x2b\x2f-\x39A-Za-z][\x30EUk]\x31vdmUtSXRlb[Q-Za-f])/
        // New-Item
        $enc08 = /(TmV\x33LUl\x30ZW[\x30-\x33]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]OZXctSXRlb[Q-Za-f]|[\x2b\x2f-\x39A-Za-z][\x30EUk]\x35ldy\x31JdGVt[\x2b\x2f-\x39A-Za-z])/
        // New-Object
        $enc09 = /(TmV\x33LU\x39iamVjd[A-P]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]OZXctT\x32JqZWN\x30[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x30EUk]\x35ldy\x31PYmplY\x33[Q-T])/
        // Out-String
        $enc10 = /(T\x33V\x30LVN\x30cmluZ[\x2b\x2f-\x39w-z]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]PdXQtU\x33RyaW\x35n[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x30EUk]\x39\x31dC\x31TdHJpbm[c-f])/
        // Remove-Item
        $enc11 = /(UmVtb\x33ZlLUl\x30ZW[\x30-\x33]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]SZW\x31vdmUtSXRlb[Q-Za-f]|[\x2b\x2f-\x39A-Za-z][\x31FVl]JlbW\x39\x32ZS\x31JdGVt[\x2b\x2f-\x39A-Za-z])/
        // Select-Object
        $enc12 = /(U\x32VsZWN\x30LU\x39iamVjd[A-P]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]TZWxlY\x33QtT\x32JqZWN\x30[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x31FVl]NlbGVjdC\x31PYmplY\x33[Q-T])/
        // Sort-Object
        $enc13 = /(U\x32\x39ydC\x31PYmplY\x33[Q-T]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]Tb\x33J\x30LU\x39iamVjd[A-P]|[\x2b\x2f-\x39A-Za-z][\x31FVl]NvcnQtT\x32JqZWN\x30[\x2b\x2f-\x39A-Za-z])/
        // Split-Path
        $enc14 = /(U\x33BsaXQtUGF\x30a[A-P]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]TcGxpdC\x31QYXRo[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x31FVl]NwbGl\x30LVBhdG[g-j])/
        // Test-Path
        $enc15 = /(VGVzdC\x31QYXRo[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]UZXN\x30LVBhdG[g-j]|[\x2b\x2f-\x39A-Za-z][\x31FVl]Rlc\x33QtUGF\x30a[A-P])/
        // Write-Host
        $enc16 = /(V\x33JpdGUtSG\x39zd[A-P]|[\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx]Xcml\x30ZS\x31Ib\x33N\x30[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x31FVl]dyaXRlLUhvc\x33[Q-T])/
        // [Convert]::FromBase64String
        $enc17 = /([\x2b\x2f-\x39A-Za-z][\x2b\x2f-\x39A-Za-z][\x31\x35\x39BFJNRVZdhlptx][\x30\x32Dlu-vy][O]jpGcm\x39tQmFzZTY\x30U\x33RyaW\x35n[\x2b\x2f-\x39A-Za-z]|[\x2b\x2f-\x39A-Za-z][\x30\x32-\x33EG-HUW-Xkm-n][\x34\x38IMQUY]\x36OkZyb\x32\x31CYXNlNjRTdHJpbm[c-f]|[QZb-d][DTjz]o\x36RnJvbUJhc\x32U\x32NFN\x30cmluZ[\x2b\x2f-\x39w-z])/
    condition:
        any of ($enc*)
}


// any office or PDF documents with a phishing hit.
// rule phish_hunter
// {
//     strings:
//         $pdf_header = "%PDF"
//     condition:
//         new_file and
//         (
//             file_type contains "office" or
//             file_type contains "pdf"    or
//             tags      contains "office" or
//             tags      contains "pdf"    or
//             $pdf_header in (0..1024)
//         )
//             and
//         (
//             signatures matches /phish/i
//         )
// }


rule APT_APT29_NOBELIUM_BoomBox_PDF_Masq_May21_1 {
    meta:
        description = "Detects PDF documents as used by BoomBox as described in APT29 NOBELIUM report"
        author = "Florian Roth"
        reference = "https://www.microsoft.com/security/blog/2021/05/27/new-sophisticated-email-based-attack-from-nobelium/"
        date = "2021-05-27"
        score = 70
    strings:
        $ah1 = { 25 50 44 46 2d 31 2e 33 0a 25 } /* PDF Header */
        $af1 = { 0a 25 25 45 4f 46 0a } /* EOF */

        $fp1 = "endobj" ascii
        $fp2 = "endstream" ascii
        $fp3 = { 20 6F 62 6A 0A } /*  obj\x0a */
    condition:
        $ah1 at 0 and $af1 at (filesize - 7) and filesize < 100KB
        and math.entropy(16, filesize) > 7
        and not 1 of ($fp*)
}


// InQuest PDF related rules
// https://github.com/InQuest/yara-rules-vt
rule Adobe_Type_1_Font {
    meta:
        author            = "InQuest Labs"
        description       = "This signature detects an Adobe Type 1 Font. The Type 1 Font Format is a standardized font format for digital imaging applications. Google's Project Zero researchers have stated publicly that any PDF using this 30+ year old font format should be regarded as suspicious."
        created_date      = "2022-03-15"
        updated_date      = "2022-03-15"
        blog_reference    = "https://www.iso.org/standard/54796.html"
        project_zero_link = "https://googleprojectzero.github.io/0days-in-the-wild/0day-RCAs/2020/CVE-2020-27930.html"
        labs_pivot        = "N/A"
        samples           = "64f2c43f3d01eae65125024797d5a40d2fdc9c825c7043f928814b85cd8201a2"
	strings:
        $pdf = "%PDF-"
        $magic_classic = "%!FontType1-1."
        $magic_next_generation1 = /obj\s*<<[^>]*\/Type\s*\/Font[^>]*\/Subtype\s*\/Type1/
        $magic_next_generation2 = /obj\s*<<[^>]*\/Subtype\s*\/Type1[^>]*\/Type\s*\/Font/
	condition:
		$magic_classic in (0..1024) or ($pdf in (0..1024) and any of ($magic_next_generation*))
}


rule PDF_Containing_JavaScript {
    meta:
        author         = "InQuest Labs"
		description    = "This signature detects a PDF file that contains JavaScript. JavaScript can be used to customize PDFs by implementing objects, methods, and properties. While not inherently malicious, embedding JavaScript inside of a PDF is often used for malicious purposes such as malware delivery or exploitation."
        created_date   = "2022-03-15"
        updated_date   = "2022-03-15"
        blog_reference = "www.sans.org/security-resources/malwarefaq/pdf-overview.php"
        labs_reference = "N/A"
        labs_pivot     = "N/A"
        samples        = "c82e29dcaed3c71e05449cb9463f3efb7114ea22b6f45b16e09eae32db9f5bef"

	strings:

		$pdf_tag1 = /\x25\x50\x44\x46\x2d/
		$js_tag1  = "/JavaScript" fullword
		$js_tag2  = "/JS"		  fullword
	condition:

		$pdf_tag1 in (0..1024) and ($js_tag1 or $js_tag2)

}


rule JS_PDF_Data_Submission {
    meta:
        author         = "InQuest Labs"
        description    = "This signature detects pdf files with http data submission forms. Severity will be 0 unless paired with Single Page PDF rule."
        created_date   = "2022-03-15"
        updated_date   = "2022-03-15"
        blog_reference = "InQuest Labs Empirical Observations"
        labs_reference = "N/A"
        labs_pivot     = "N/A"
        samples        = "a0adbe66e11bdeaf880b81b41cd63964084084a413069389364c98da0c4d2a13"
	strings:
        $pdf_header = "%PDF-"
        $js = /(\/JS|\/JavaScript)/ nocase
        $a1 = /app\s*\.\s*doc\s*\.\s*submitForm\s*\(\s*['"]http/ nocase
        $inq_tail = "INQUEST-PP=pdfparser"
	condition:
        ($pdf_header in (0..1024) or $inq_tail in (filesize-30..filesize))
            and $js
            and $a1
}


rule PDF_Launch_Action_EXE {
    meta:
        author         = "InQuest Labs"
        description    = "This signature detects PDF files that launch an executable upon being opened on a host machine. This action is performed by the Launch Action feature available in the PDF file format and is commonly abused by threat actors to execute delivered malware."
        created_date   = "2022-03-15"
        updated_date   = "2022-03-15"
        blog_reference = "InQuest Labs Empirical Observations"
        labs_reference = "N/A"
        labs_pivot     = "N/A"
        samples        = "cb5e659c4ac93b335c77c9b389d8ef65d8c20ab8b0ad08e5f850cc5055e564c3"
	strings:
        /* 8 0 obj
        <<
        /Type /Action
        /S /Launch
        /Win
        <<
        /F (cmd.exe)
        >>
        >>
        endobj
        */
        $magic01 = "INQUEST-PP=pdfparser"
        $magic02 = "%PDF"

        $re1 = /\x2fType[ \t\r\n]*\x2fAction/ nocase wide ascii
        $re2 = /obj[^\x3c\x3e]+<<[^\x3e]*\x2fS[ \t\r\n]*\x2fLaunch[^\x3c\x3e]*<<[^\x3e]*\x2fF[ \t\r\n]*\x28[^\x29]+\.exe[^\x29]*\x29/ nocase wide ascii
	condition:
        ($magic01 in (filesize-30 .. filesize) or $magic02 in (0 .. 10)) and all of ($re*)
}


rule PDF_Launch_Function {
    meta:
        author         = "InQuest Labs"
		description    = "This signature detects the launch function within a PDF file. This function allows a document author to attach an executable file."
        created_date   = "2022-03-15"
        updated_date   = "2022-03-15"
        blog_reference = "http://blog.trendmicro.com/trendlabs-security-intelligence/PDF-launch-feature-abused-to-carry-zeuszbot/"
        labs_reference = "N/A"
        labs_pivot     = "N/A"
        samples        = "c2f2d1de6bf973b849725f1069c649ce594a907c1481566c0411faba40943ee5"
	strings:
		$pdf_header = "%PDF-"
		$launch = "/Launch" nocase
	condition:
		$pdf_header in (0..1024) and $launch

}


rule PDF_with_Embedded_RTF_OLE_Newlines {
    meta:
        author         = "InQuest Labs"
        description    = "This signature detects suspicious PDF files embedded with RTF files that contain embedded OLE content that injects newlines into embedded OLE contents as a means of payload obfuscation and detection evasion."
        created_date   = "2022-03-15"
        updated_date   = "2022-03-15"
        blog_reference = "InQuest Internal Research"
        labs_reference = "N/A"
        labs_pivot     = "N/A"
        samples        = "d784c53b8387f1e2f1bcb56a3604a37b431638642e692540ebeaeee48c1f1a07"

 	strings:
		$rtf_magic = "{\\rt"  // note that {\rtf1 is not required
        $rtf_objdata = /\x7b[^\x7d]*\\objdata/ nocase
        $nor = "D0CF11E0A1B11AE1" nocase
        $obs = /D[ \r\t\n]*0[ \r\t\n]*C[ \r\t\n]*F[ \r\t\n]*1[ \r\t\n]*1[ \r\t\n]*E[ \r\t\n]*0[ \r\t\n]*A[ \r\t\n]*1[ \r\t\n]*B[ \r\t\n]*1[ \r\t\n]*1[ \r\t\n]*A[ \r\t\n]*E[ \r\t\n]*1/ nocase
	condition:
		$rtf_magic and $rtf_objdata and ($obs and not $nor)
}

/*
This signature detects Adobe PDF files that reference a remote UNC object for the purpose of leaking NTLM hashes.
New methods for NTLM hash leaks are discovered from time to time. This particular one is triggered upon opening of a
malicious crafted PDF. Original write-up from CheckPoint:

    https://research.checkpoint.com/ntlm-credentials-theft-via-pdf-files/

Public proof-of-concepts:

    https://github.com/deepzec/Bad-Pdf
    https://github.com/3gstudent/Worse-PDF

Requirements:
    /AA for Auto Action
    /O for open is functionally equivalent to /C for close.
    /S + /GoToE (Embedded) can be swapped with /GoToR (Remote).
    /D location reference.
    /F the UNC reference.

Multiple different arrangements, example one:

    /AA <<
        /O <<
            /F (\\\\10.20.30.40\\test)
            /D [ 0 /Fit]
            /S /GoToR
            >>
example two:

    /AA <<
        /C <<
            /D [ 0 /Fit]
            /S /GoToE
            /F (\\\\10.20.30.40\\test)
            >>

example three:

    /AA <<
        /O <<
            /D [ 0 /Fit]
            /F (\\\\10.20.30.40\\test)
            /S /GoToR
            >>

Multiple protocols supported for the /F include, both http and UNC.
*/

rule NTLM_Credential_Theft_via_PDF {
    meta:
        Author      = "InQuest Labs"
        URL         = "https://github.com/InQuest/yara-rules"
        Description = "This signature detects Adobe PDF files that reference a remote UNC object for the purpose of leaking NTLM hashes."
    strings:
        // we have three regexes here so that we catch all possible orderings but still meet the requirement of all three parts.
        $badness1 = /\s*\/AA\s*<<\s*\/[OC]\s*<<((\s*\/\D\s*\[[^\]]+\])(\s*\/S\s*\/GoTo[ER])|(\s*\/S\s*\/GoTo[ER])(\s*\/\D\s*\[[^\]]+\]))\s*\/F\s*\((\\\\\\\\[a-z0-9]+\.[^\\]+\\\\[a-z0-9]+|https?:\/\/[^\)]+)\)/ nocase
        $badness2 = /\s*\/AA\s*<<\s*\/[OC]\s*<<\s*\/F\s*\((\\\\\\\\[a-z0-9]+\.[^\\]+\\\\[a-z0-9]+|https?:\/\/[^\)]+)\)((\s*\/\D\s*\[[^\]]+\])(\s*\/S\s*\/GoTo[ER])|(\s*\/S\s*\/GoTo[ER])(\s*\/\D\s*\[[^\]]+\]))/ nocase
        $badness3 = /\s*\/AA\s*<<\s*\/[OC]\s*<<((\s*\/\D\s*\[[^\]]+\])\s*\/F\s*\((\\\\\\\\[a-z0-9]+\.[^\\]+\\\\[a-z0-9]+|https?:\/\/[^\)]+)\)(\s*\/S\s*\/GoTo[ER])|(\s*\/S\s*\/GoTo[ER])\s*\/F\s*\(\\\\\\\\[a-z0-9]+.[^\\]+\\\\[a-z0-9]+\)(\s*\/\D\s*\[[^\]]+\]))/ nocase
    condition:
        for any i in (0..1024) : (uint32be(i) == 0x25504446) and any of ($badness*)
}


rule PDF_with_Launch_Action_Function
{
    meta:
        author         = "InQuest Labs"
        description    = "This signature detects the launch function within a PDF file. This function allows the document author to attach an executable file."
        created_date   = "2022-03-15"
        updated_date   = "2022-03-15"
        blog_reference = "http://blog.didierstevens.com/2010/03/29/escape-from-pdf/"
        labs_reference = "N/A"
        labs_pivot     = "N/A"
        samples        = "a9fbb50dedfd84e1f4a3507d45b1b16baa43123f5ae98dae6aa9a5bebeb956a8"
	strings:
		$pdf_header = "%PDF-"
		$a = "<</S/Launch/Type/Action/Win<</F"
	condition:
		$pdf_header in (0..1024) and $a
}


rule PDF_JS_guillemet_close_in_Adobe_Type1_font
{
    meta:
        author             = "Michel de Cryptadamus"
        description        = "Found in a PDF that caused a security breach. Exact mechanism unknown but /F means URL, JS is JS, backticks are backticks, and bb is the closing guillemet quote (the one used in PDF docs to close objects). Taken together the sequence is basically shorthand PDF speak for \"close the PDF object prematurely\"."
        created_date       = "2022-10-01"
        updated_date       = "2022-10-01"
        blog_reference     = "https://twitter.com/Cryptadamist/status/1570167937381826560"
        breach_description = "https://cryptadamus.substack.com/p/the-hack-at-the-end-of-the-universe"
        samples            = "61d47fbfe855446d77c7da74b0b3d23dbcee4e4e48065a397bbf09a7988f596e"
        in_the_wild        = true
	strings:
        // "/FJS`\xbb`"
		$url_js_backtick_close_obj = {2F 46 4A 53 60 BB 60}
	condition:
        $url_js_backtick_close_obj and Adobe_Type_1_Font
}

