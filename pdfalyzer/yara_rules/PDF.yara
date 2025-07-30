import "hash"
import "math"
import "pe"


// rule pdf: PDF
// {
//     meta:
//         author = "Jaume Martin"
//         description = "Matches '%PDF' to '%%EOF'. Works even on raw bytes (e.g. raw dd image of a drive)"
//         reference = "https://github.com/Xumeiquer/yara-forensics/blob/bccefe4bac824956cd0694b6681a2d555bf6b0fe/raw/pdf.yar"

//     strings:
//         $pdf_start = {25 50 44 46}
//         $eof1 = {0A 25 25 45 4F 46 (??|0A)}
//         $eof2 = {0D 0A 25 25 45 4F 46 0D 0A}
//         $eof3 = {0D 25 25 45 4F 46 0D}

//     condition:
//        $pdf_start and for any of ($eof1, $eof2, $eof3): ( @ > @pdf_start )
// }


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


rule PDF_Embedded_Exe : PDF {
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


rule malicious_author : PDF {
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
        $magic in (0..1024) and all of ($reg*)
}


rule suspicious_version : PDF {
    meta:
        author = "Glenn Edwards (@hiddenillusion)"
        version = "0.1"
        weight = 3

    strings:
        $magic = { 25 50 44 46 }
        $ver = /%PDF-1.\d{1}/
    condition:
        $magic in (0..1024) and not $ver
}


rule suspicious_creation : PDF {
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
        $magic in (0..1024) and $header and 1 of ($create*)
}


rule suspicious_title : PDF {
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
        $magic in (0..1024) and $header and 1 of ($title*)
}


rule suspicious_author : PDF {
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
        $magic in (0..1024) and $header and 1 of ($author*)
}


rule suspicious_producer : PDF {
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
        $magic in (0..1024) and $header and 1 of ($producer*)
}


rule suspicious_creator : PDF {
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
        $magic in (0..1024) and $header and 1 of ($creator*)
}


rule shellcode_blob_metadata : PDF {
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
        $magic in (0..1024) and 1 of ($reg*)
}


rule multiple_filtering : PDF {
    meta:
        author = "Glenn Edwards (@hiddenillusion)"
        version = "0.2"
        weight = 3
    strings:
        $magic = { 25 50 44 46 }
        $attrib = /\/Filter.*?(\/ASCIIHexDecode\W+?|\/LZWDecode\W+?|\/ASCII85Decode\W+?|\/FlateDecode\W+?|\/RunLengthDecode){2}?/
        // left out: /CCITTFaxDecode, JBIG2Decode, DCTDecode, JPXDecode, Crypt
    condition:
        $magic in (0..1024) and $attrib
}


rule suspicious_launch_action : PDF {
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
        $magic in (0..1024) and 3 of ($attrib*)
}


rule suspicious_embed : PDF {
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
        $magic in (0..1024) and 1 of ($meth*) and 2 of ($attrib*)
}


rule suspicious_obfuscation : PDF {
    meta:
        author = "Glenn Edwards (@hiddenillusion)"
        version = "0.1"
        weight = 2
    strings:
        $magic = { 25 50 44 46 }
        $reg = /\/\w#[a-zA-Z0-9]{2}#[a-zA-Z0-9]{2}/
    condition:
        $magic in (0..1024) and #reg > 5
}


rule invalid_XObject_js : PDF {
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
        $magic in (0..1024) and not $ver and all of ($attrib*)
}


rule invalid_trailer_structure : PDF {
    meta:
        author = "Glenn Edwards (@hiddenillusion), @malvidin"
        version = "0.2"
        weight = 1
    strings:
        $magic = "%PDF"  // Required for a valid PDF
        $reg0 = /trailer[ \r\n]*<<.{0,1000}\/Size\b/s
        $reg1 = /\/Root\b.{0,1000}[ \r\n]*.{0,500}startxref[ \r\n]*.{0,500}[ \r\n]*%%EOF/s
    condition:
        $magic in (0..1024) and not ($reg0 or $reg1)
}


rule multiple_versions : PDF {
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
        $magic in (0..1024) and #trailer > 1 and #eof > 1
}


rule js_wrong_version : PDF {
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
        $magic in (0..1024) and $js and not $ver
}


rule JBIG2_wrong_version : PDF {
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
        $magic in (0..1024) and $js and not $ver
}


rule FlateDecode_wrong_version : PDF {
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
        $magic in (0..1024) and $js and not $ver
}


rule embed_wrong_version : PDF {
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
        $magic in (0..1024) and $embed and not $ver
}


rule invalid_xref_numbers : PDF {
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
        $magic in (0..1024) and not $reg0 and not $reg1
}


rule js_splitting : PDF {
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
        $magic in (0..1024) and $js and 1 of ($s*)
}


rule header_evasion : PDF {
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


rule BlackHole_v2 : PDF {
    meta:
        author = "Glenn Edwards (@hiddenillusion)"
        version = "0.1"
        ref = "http://fortknoxnetworks.blogspot.no/2012/10/blackhhole-exploit-kit-v-20-url-pattern.html"
        weight = 3

    strings:
        $magic = { 25 50 44 46 }
        $content = "Index[5 1 7 1 9 4 23 4 50"
    condition:
        $magic in (0..1024) and $content
}

rule blackhole2_pdf : EK PDF{
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

rule XDP_embedded_PDF : PDF {
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


rule PDF_Document_with_Embedded_IQY_File {
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


rule Base64_Encoded_Powershell_Directives {
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


rule PDF_JS_guillemet_close_in_Adobe_Type1_font {
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


rule rule_pdf_activemime {
    meta:
        author = "Didier Stevens"
        date = "2023/08/29"
        version = "0.0.1"
        samples = "5b677d297fb862c2d223973697479ee53a91d03073b14556f421b3d74f136b9d,098796e1b82c199ad226bff056b6310262b132f6d06930d3c254c57bdf548187,ef59d7038cfd565fd65bae12588810d5361df938244ebad33b71882dcf683058"
        description = "look for files that start with %PDF- and contain BASE64 encoded string ActiveMim (QWN0aXZlTWlt), possibly obfuscated with extra whitespace characters"
        usage = "if you don't have to care about YARA performance warnings, you can uncomment string $base64_ActiveMim0 and remove all other $base64_ActiveMim## strings"
    strings:
        $pdf = "%PDF-"
//        $base64_ActiveMim0 = /[ \t\r\n]*Q[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim1 = /Q  [ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim2 = /Q \t[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim3 = /Q \r[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim4 = /Q \n[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim5 = /Q\t [ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim6 = /Q\t\t[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim7 = /Q\t\r[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim8 = /Q\t\n[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim9 = /Q\r [ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim10 = /Q\r\t[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim11 = /Q\r\r[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim12 = /Q\r\n[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim13 = /Q\n [ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim14 = /Q\n\t[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim15 = /Q\n\r[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim16 = /Q\n\n[ \t\r\n]*W[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim17 = /QW [ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim18 = /QW\t[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim19 = /QW\r[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim20 = /QW\n[ \t\r\n]*N[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
        $base64_ActiveMim21 = /QWN[ \t\r\n]*0[ \t\r\n]*a[ \t\r\n]*X[ \t\r\n]*Z[ \t\r\n]*l[ \t\r\n]*T[ \t\r\n]*W[ \t\r\n]*l[ \t\r\n]*t/
    condition:
        $pdf at 0 and any of ($base64_ActiveMim*)
}


rule malware_MaldocinPDF {
    meta:
        author         = "Yuma Masubuchi and Kota Kino"
        description    = "Search for embeddings of malicious Word files into a PDF file."
        created_date   = "2023-08-15"
        blog_reference = "https://blogs.jpcert.or.jp/en/2023/08/maldocinpdf.html"
        labs_reference = "N/A"
        labs_pivot     = "N/A"
        samples        = "ef59d7038cfd565fd65bae12588810d5361df938244ebad33b71882dcf683058"
    strings:
        $docfile2 = "<w:WordDocument>" ascii nocase
        $xlsfile2 = "<x:ExcelWorkbook>" ascii nocase
        $mhtfile0 = "mime" ascii nocase
        $mhtfile1 = "content-location:" ascii nocase
        $mhtfile2 = "content-type:" ascii nocase
     condition:
        (uint32(0) == 0x46445025) and
        (1 of ($mhtfile*)) and
        ( (1 of ($docfile*)) or
          (1 of ($xlsfile*)) )
}


rule EXPLOIT_PDFJS_CVE_2024_4367 {
    meta:
        description = "Detects PDFs that exploit CVE-2024-4367"
        author = "spaceraccoon, Eugene Lim"
        blog_reference = "https://codeanlabs.com/blog/research/cve-2024-4367-arbitrary-js-execution-in-pdf-js/"
        reference = "https://github.com/spaceraccoon/detect-cve-2024-4367"
        date = "2024-05-23"
        modified = "2024-05-23"
        score = 75
        id = "bb000216-17b5-41eb-a144-2982131fbf45"
    strings:
        $re1 = /\/FontMatrix\s+\[\.\-\d\s]*\(/
    condition:
        any of them
}


rule QakbotPDF {
    meta:
        description = "This is a rule to detect Qakbot"
        hash = "ce0b6e49d017a570bdaa463e51893014a7378fb4586e33fabbc6c4832c355663"
        filename = "Necessitatibus.pdf"
        author = "Motawkkel Abdulrhman AKA RY0D4N"
        reference = "https://github.com/xRY0D4N/Yara-Rules/blob/main/Qakbot/rule.yar"
    strings:
        $url = "/URI (http://gurtek.com.tr/exi/exi.php)" nocase ascii wide
    condition:
        $url
}


rule GIFTEDCROOK {
    meta:
        date = "2025-06-29"
        description = "Find GIFTEDCROOK PDFs"
        hash = "1974709f9af31380f055f86040ef90c71c68ceb2e14825509babf902b50a1a4b"
        reference = "https://arcticwolf.com/resources/blog/giftedcrook-strategic-pivot-from-browser-stealer-to-data-exfiltration-platform/"
    strings:
        $mega_link = "https://mega.nz/file" nocase
        $creator = "FEFF005700720069007400650072"
    condition:
        uint32(0) == 0x25504446 and
        any of them
}


rule PK_AdobePDF_hse : Adobe {
    meta:
        description = "Phishing Kit impersonating Adobe PDF online"
        licence = "GPL-3.0"
        author = "Thomas 'tAd' Damonneville"
        date = "2021-07-25"
        comment = "Phishing Kit - Adobe PDF Online - 'Hades Silent Exploits'"
    strings:
        // the zipfile working on
        $zip_file = { 50 4b 03 04 }
        // specific directory found in PhishingKit
        $spec_dir = "adobe"
        // specific file found in PhishingKit
        $spec_file = "index.php"
        $spec_file2 = "login.php"
        $spec_file3 = "logg.html"
    condition:
        // look for the ZIP header
        uint32(0) == 0x04034b50 and
        // make sure we have a local file header
        $zip_file and
        $spec_dir and
        // check for file
        all of ($spec_file*)
}


rule PK_AdobePDF_antenna : Adobe {
    meta:
        description = "Phishing Kit impersonating Adobe PDF Online"
        licence = "AGPL-3.0"
        author = "Thomas 'tAd' Damonneville"
        reference = ""
        date = "2024-04-15"
        comment = "Phishing Kit - Adobe PDF Online - contain antenna.css file"
    strings:
        // the zipfile working on
        $zip_file = { 50 4b 03 04 }
        // specific directory found in PhishingKit
        $spec_dir = "core"
        // specific file found in PhishingKit
        $spec_file = "antenna.css"
        $spec_file2 = "screenshot_23.png"
        $spec_file3 = "fx.js"
        $spec_file4 = "post.php"
        $spec_file5 = "22222222222.png"
        $spec_file6 = "gh-adobe-impersonation-scam-loginwindow.png"
    condition:
        // look for the ZIP header
        uint32(0) == 0x04034b50 and
        // make sure we have a local file header
        $zip_file and
        all of ($spec_dir*) and
        // check for file
        all of ($spec_file*)
}


rule PK_AdobePDF_dotloop : Adobe {
    meta:
        description = "Phishing Kit impersonating Adobe PDF Online"
        licence = "AGPL-3.0"
        author = "Thomas 'tAd' Damonneville"
        date = "2024-08-28"
        comment = "Phishing Kit - Adobe PDF Online - 'From: Dotloop'"
    strings:
        // the zipfile working on
        $zip_file = { 50 4b 03 04 }
        // specific directory found in PhishingKit
        $spec_dir = "asset"
        // specific file found in PhishingKit
        $spec_file = "signin.php"
        $spec_file2 = "contract.jpg"
        $spec_file3 = "Microsoft_Edge_logo_(2019).svg.png"
        $spec_file4 = "KYC-ENG (confidential).pdf"
    condition:
        // look for the ZIP header
        uint32(0) == 0x04034b50 and
        // make sure we have a local file header
        $zip_file and
        all of ($spec_dir*) and
        // check for file
        all of ($spec_file*)
}


rule APT_NGO_wuaclt_PDF{
    meta:
        author = "AlienVault Labs"
        license = "GPL-2.0"
        reference = "https://github.com/alankrit29/signature-base/blob/4f8c5d7e39ee5c369c42b89e765d552e5dbafb23/APT_NGO.yar#L30"
    strings:
        $pdf = "%PDF" nocase
        $comment = {3C 21 2D 2D 0D 0A 63 57 4B 51 6D 5A 6C 61 56 56 56 56 56 56 56 56 56 56 56 56 56 63 77 53 64 63 6A 4B 7A 38 35 6D 37 4A 56 6D 37 4A 46 78 6B 5A 6D 5A 6D 52 44 63 5A 58 41 73 6D 5A 6D 5A 7A 42 4A 31 79 73 2F 4F 0D 0A}
    condition:
        $pdf at 0 and $comment in (0..200)
}


rule LokiBot_Dropper_ScanCopyPDF_Feb18 {
   meta:
      description = "Auto-generated rule - file Scan Copy.pdf.com (https://github.com/alankrit29/signature-base/blob/4f8c5d7e39ee5c369c42b89e765d552e5dbafb23/crime_loki_bot.yar)"
      license = "https://creativecommons.org/licenses/by-nc/4.0/"
      author = "Florian Roth"
      reference = "https://app.any.run/tasks/401df4d9-098b-4fd0-86e0-7a52ce6ddbf5"
      date = "2018-02-14"
      hash1 = "6f8ff26a5daf47effdea5795cdadfff9265c93a0ebca0ce5a4144712f8cab5be"
   strings:
      $x1 = "Win32           Scan Copy.pdf   " fullword wide
      $a1 = "C:\\Program Files (x86)\\Microsoft Visual Studio\\VB98\\VB6.OLB" fullword ascii
      $s1 = "Compiling2.exe" fullword wide
      $s2 = "Unstalled2" fullword ascii
      $s3 = "Compiling.exe" fullword wide
   condition:
      uint16(0) == 0x5a4d and filesize < 1000KB and $x1 or
      ( $a1 and 1 of ($s*) )
}


rule Docm_in_PDF {
   meta:
      description = "Detects an embedded DOCM in PDF combined with OpenAction"
      license = "https://creativecommons.org/licenses/by-nc/4.0/"
      author = "Florian Roth"
      reference = "Internal Research https://github.com/alankrit29/signature-base/blob/4f8c5d7e39ee5c369c42b89e765d552e5dbafb23/general_officemacros.yar"
      date = "2017-05-15"
   strings:
      $a1 = /<<\/Names\[\([\w]{1,12}.docm\)/ ascii
      $a2 = "OpenAction" ascii fullword
      $a3 = "JavaScript" ascii fullword
   condition:
      uint32(0) == 0x46445025 and all of them
}


rule HKTL_EmbeddedPDF {
   meta:
      description = "Detects Embedded PDFs which can start malicious content (https://github.com/alankrit29/signature-base/blob/4f8c5d7e39ee5c369c42b89e765d552e5dbafb23/thor-hacktools.yar#L4437)"
      author = "Tobias Michalski"
      reference = "https://twitter.com/infosecn1nja/status/1021399595899731968?s=12"
      date = "2018-07-25"
   strings:
      $x1 = "/Type /Action\n /S /JavaScript\n /JS (this.exportDataObject({" fullword ascii
      $s1 = "(This PDF document embeds file" fullword ascii
      $s2 = "/Names << /EmbeddedFiles << /Names" fullword ascii
      $s3 = "/Type /EmbeddedFile" fullword ascii
   condition:
      uint16(0) == 0x5025 and
      2 of ($s*) and $x1
}


rule suspicious_js {
    meta:
        severity = 6
        type = "pdf"
        author = "Glenn Edwards (@hiddenillusion)"
        version = "0.1"
        weight = 3
        description = "possible exploit"
        reference = "https://github.com/a232319779/mmpi/blob/master/mmpi/data/yara/pdf/pdf.yara"
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


rule possible_exploit {
    meta:
        severity = 9
        type = "pdf"
        author = "Glenn Edwards (@hiddenillusion)"
        version = "0.1"
        weight = 3
        url = "https://github.com/hiddenillusion/AnalyzePDF/blob/master/pdf_rules.yara"
        description = "possible exploit"
        reference = "https://github.com/a232319779/mmpi/blob/master/mmpi/data/yara/pdf/pdf.yara"
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


rule Detect_JavaScript {
    meta:
        description = "Detects embedded JavaScript in PDF files"
        type = "JavaScript"
    strings:
        $js1 = /\/JavaScript/i
        $js2 = /\/JS/i
        $js3 = /\/AA\s*<<\s*\/O\s*<<\s*\/S\s*\/JavaScript\s*\/JS\s*\(/i
        $js4 = /app\.alert/i
        $js5 = /this\.execute/i
        $js6 = /this\.print/i
        $js7 = /this\.saveAs/i
        $js8 = /util\.printd/i
        $js9 = /app\.setTimeOut/i
        $js10 = /event\.target/i
    condition:
        $js1 or $js2 or $js3 or $js4 or $js5 or $js6 or $js7 or $js8 or $js9 or $js10
}


rule Detect_Launch_Action {
    meta:
        description = "Detects Launch actions in PDF files"
        type = "Launch"
    strings:
        $launch1 = /\/Launch/i
        $launch2 = /\/Action\s*>>\s*\/Type\s*\/Action/i
        $launch3 = /\/S\s*\/Launch/i
        $launch4 = /\/Launch\s*<<\s*\/S\s*\/Launch/i
        $launch5 = /\/Launch\s*<<\s*\/F\s*<<\s*\/S\s*\/Launch/i
        $launch6 = /\/Launch\s*\/F\s*\(/i
        $launch7 = /\/Launch\s*<<\s*\/F\s*\(/i
        $launch8 = /\/Launch\s*<<\s*\/Win\s*\(/i
        $launch9 = /\/Launch\s*<<\s*\/Mac\s*\(/i
        $launch10 = /\/Launch\s*\/Win\s*\(/i
    condition:
        $launch1 or $launch2 or $launch3 or $launch4 or $launch5 or $launch6 or $launch7 or $launch8 or $launch9 or $launch10
}


rule Detect_OpenAction {
    meta:
        description = "Detects OpenAction in PDF files"
        type = "OpenAction"
    strings:
        $openAction1 = /\/OpenAction/i
        $openAction2 = /\/AA/i
        $openAction3 = /\/OpenAfterSave/i
        $openAction4 = /\/OpenDocument/i
        $openAction5 = /\/Open/i
        $openAction6 = /\/O\s*<<\s*\/S\s*\/JavaScript\s*\/JS\s*\(/i
        $openAction7 = /\/O\s*<<\s*\/S\s*\/JavaScript\s*\/JS/i
        $openAction8 = /\/O\s*<<\s*\/JS\s*\(/i
        $openAction9 = /\/O\s*<<\s*\/JS/i
        $openAction10 = /\/Open\s*<<\s*\/JavaScript\s*\/JS\s*\(/i
    condition:
        $openAction1 or $openAction2 or $openAction3 or $openAction4 or $openAction5 or $openAction6 or $openAction7 or $openAction8 or $openAction9 or $openAction10
}


rule Detect_Embedded_Files {
    meta:
        description = "Detects embedded files in PDF files"
        type = "EmbeddedFile"
    strings:
        $embed1 = /\/EmbeddedFile/i
        $embed2 = /\/FileAttachment/i
        $embed3 = /\/Type\s*\/EmbeddedFile/i
        $embed4 = /\/EF\s*<<\s*\/F\s*<<\s*\/Type\s*\/EmbeddedFile/i
        $embed5 = /\/EmbeddedFile\s*<<\s*\/Type\s*\/EmbeddedFile/i
        $embed6 = /\/Filespec\s*<<\s*\/EF\s*<<\s*\/F\s*<<\s*\/Type\s*\/EmbeddedFile/i
        $embed7 = /\/EmbeddedFile\s*\/Filespec/i
        $embed8 = /\/EmbeddedFile\s*\/Names/i
        $embed9 = /\/EmbeddedFile\s*\/Names\s*<<\s*\/Type\s*\/EmbeddedFile/i
        $embed10 = /\/EmbeddedFile\s*\/Names\s*<<\s*\/Type\s*\/EmbeddedFile\s*\/Filespec/i
    condition:
        $embed1 or $embed2 or $embed3 or $embed4 or $embed5 or $embed6 or $embed7 or $embed8 or $embed9 or $embed10
}


rule Detect_Shellcode {
    meta:
        description = "Detects suspicious shellcode patterns in PDF files"
        type = "Shellcode"
    strings:
        $shellcode1 = { 6a 60 68 63 61 6c 63 54 59 66 83 e9 ff 33 d2 64 8b 52 30 8b 52 0c 8b 52 14 8b 72 28 }
        $shellcode2 = { 31 c0 50 68 2e 65 78 65 68 63 61 6c 63 8b dc 88 04 24 50 53 51 52 83 ec 04 }
        $shellcode3 = { 50 51 52 56 57 53 89 e5 83 e4 f0 31 c0 64 8b 40 30 8b 40 0c 8b 70 1c ad 8b 40 08 }
        $shellcode4 = { 89 e5 81 ec a0 00 00 00 31 c0 50 50 50 50 40 89 e1 50 89 e2 57 51 52 50 83 ec 04 }
        $shellcode5 = { 31 c0 50 68 2e 64 61 74 61 68 5c 64 61 74 61 68 63 61 6c 63 89 e3 8b 53 3c }
        $shellcode6 = { 31 d2 52 68 78 2e 74 78 68 2e 64 61 74 68 5c 5c 5c 68 2e 5c 5c 5c 68 5c 5c 5c }
        $shellcode7 = { 68 5c 61 5c 61 5c 61 68 74 2e 74 78 68 2e 64 61 74 68 5c 5c 5c 68 2e 5c 5c 5c }
        $shellcode8 = { 68 5c 61 5c 61 5c 61 68 78 2e 74 78 68 2e 64 61 74 68 5c 5c 5c 68 2e 5c 5c 5c }
        $shellcode9 = { 68 61 5c 61 5c 68 61 5c 68 74 2e 78 68 2e 61 74 68 5c 5c 68 2e 5c 68 5c 5c }
        $shellcode10 = { 68 61 5c 61 5c 61 68 74 2e 74 68 2e 64 68 5c 5c 5c 68 2e 5c 5c 68 5c 5c 68 }
    condition:
        $shellcode1 or $shellcode2 or $shellcode3 or $shellcode4 or $shellcode5 or $shellcode6 or $shellcode7 or $shellcode8 or $shellcode9 or $shellcode10
}


rule Detect_URLs {
    meta:
        description = "Detects suspicious URLs in PDF files"
        type = "URL"
    strings:
        $url1 = /ftp:\/\/[^\s]+/ nocase
        $url2 = /file:\/\/[^\s]+/ nocase
        $url3 = /:\/\/[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/ nocase
    condition:
        $url1 or $url2 or $url3
}


rule Detect_PDF_Embedded_Files {
    meta:
        atk_type = "Macro"
        description = "Detects embedded files in PDF files"
        author = "groommang"
        date = "2024-06-25"
    strings:
        $pdf_header = {25 50 44 46}
        $embedded_file = /EmbeddedFile/
    condition:
        $pdf_header at 0 and $embedded_file
}


rule Detect_PDF_Suspicious_AcroForms {
    meta:
          atk_type = "Macro"
        description = "Detects suspicious AcroForms in PDF files"
        author = "groommang"
        date = "2024-06-25"
    strings:
        $pdf_header = {25 50 44 46}
        $acroform = /AcroForm/
    condition:
        $pdf_header at 0 and $acroform
}


rule oAuth_Phishing_PDF {
    meta:
        description = "Identifies potential phishing PDFs that target oAuth."
        id = "789YmThaTvLDaE1V2Oqx7q"
        fingerprint = "c367bca866de0b066e291b4e45216cbb68cc23297b002a29ca3c8d640a7db78e"
        version = "1.0"
        creation_date = "2022-01-01"
        first_imported = "2022-02-03"
        last_modified = "2025-03-10"
        status = "RELEASED"
        sharing = "TLP:WHITE"
        source = "BARTBLAZE"
        author = "@bartblaze"
        category = "MALWARE"
        reference = "https://twitter.com/ffforward/status/1484127442679836676"
    strings:
        $pdf = {25504446} //%PDF
        $s1 = "/URI (https://login.microsoftonline.com/common/oauth2/" nocase
        $s2 = "/URI (https://login.microsoftonline.com/consumers/oauth2" nocase
        $s3 = "/URI (https://accounts.google.com/o/oauth2" nocase
    condition:
        $pdf at 0 and any of ($s*)
}


rule Adobe_XMP_Identifier {
    meta:
        author         = "InQuest Labs"
        description    = "This signature identifies Adobe Extensible Metadata Platform (XMP) identifiers embedded within files. Defined as a standard for mapping graphical asset relationships, XMP allows for tracking of both parent-child relationships and individual revisions. There are three categories of identifiers: original document, document, and instance. Generally, XMP data is stored in XML format, updated on save/copy, and embedded within the graphical asset. These identifiers can be used to track both malicious and benign graphics within common Microsoft and Adobe document lures."
        created_date   = "2022-03-15"
        updated_date   = "2022-03-15"
        blog_reference = "http://wwwimages.adobe.com/content/dam/acom/en/products/xmp/Pdfs/XMPAssetRelationships.pdf"
        labs_reference = "https://labs.inquest.net/dfi/sha256/1030710f6f18950f01b1a55d50a5169717e48567aa13a0a769f5451423280b4d"
        labs_pivot     = "https://labs.inquest.net/dfi/search/ioc/xmpid/xmp.did%3AEDC9411A6A5F11E2838BB9184F90E845##eyJyZXN1bHRzIjpbIn4iLCJmaXJzdFNlZW4iLDEsIiIsW11dfQ=="
        samples        = "1030710f6f18950f01b1a55d50a5169717e48567aa13a0a769f5451423280b4d"
    strings:
        $xmp_md5  = /xmp\.[dio]id[-: _][a-f0-9]{32}/  nocase ascii wide
        $xmp_guid = /xmp\.[dio]id[-: _][a-f0-9]{36}/ nocase ascii wide
    condition:
        any of them
}


rule Generic_Phishing_PDF {
    meta:
        atk_type = "Generic_Phishing_PDF"
        id = "6iE0XEqqhVGNED6Z8xIMr1"
        fingerprint = "f3f31ec9651ee41552d41dbd6650899d7a33beea46ed1c3329c3bbd023fe128e"
        version = "1.0"
        creation_date = "2019-03-01"
        first_imported = "2021-12-30"
        last_modified = "2021-12-30"
        status = "RELEASED"
        sharing = "TLP:WHITE"
        source = "BARTBLAZE"
        author = "@bartblaze"
        description = "Identifies generic phishing PDFs."
        category = "MALWARE"
        reference = "https://bartblaze.blogspot.com/2019/03/analysing-massive-office-365-phishing.html"
    strings:
        $pdf = {25504446}
        $s1 = "<xmp:CreatorTool>RAD PDF</xmp:CreatorTool>"
        $s2 = "<x:xmpmeta xmlns:x=\"adobe:ns:meta/\" x:xmptk=\"DynaPDF"
    condition:
        $pdf at 0 and all of ($s*)
}


rule Embedded_EXE_Cloaking : maldoc {
    meta:
        description = "Detects an embedded executable in a non-executable file"
        author = "Florian Roth"
        date = "2015/02/27"
        score = 80
    strings:
        $noex_png = { 89 50 4E 47 }
        $noex_pdf = { 25 50 44 46 }
        $noex_rtf = { 7B 5C 72 74 66 31 }
        $noex_jpg = { FF D8 FF E0 }
        $noex_gif = { 47 49 46 38 }
        $mz  = { 4D 5A }
        $a1 = "This program cannot be run in DOS mode"
        $a2 = "This program must be run under Win32"
    condition:
        (
            ( $noex_png at 0 ) or
            ( $noex_pdf at 0 ) or
            ( $noex_rtf at 0 ) or
            ( $noex_jpg at 0 ) or
            ( $noex_gif at 0 )
        )
        and
        for any i in (1..#mz): ( @a1 < ( @mz[i] + 200 ) or @a2 < ( @mz[i] + 200 ) )
}


rule PDF_EMBEDDED_DOCM {
    meta:
        description = "Find pdf files that have an embedded docm with openaction"
        author = "Brian Carter"
        last_modified = "May 11, 2017"
    strings:
        $magic = { 25 50 44 46 2d }
        $txt1 = "EmbeddedFile"
        $txt2 = "docm)"
        $txt3 = "JavaScript" nocase
    condition:
        $magic at 0 and all of ($txt*)
}


rule pdf_fake_password {
    meta:
        date = "2022-11-23"
        description = "Detects PDF obfuscated via /Encrypt and /AuthEvent/DocOpen but opens without password"
        author = "Paul Melson @pmelson"
        hash = "0e182afae5301ac3097ae3955aa8c894ec3a635acbec427d399ccc4aac3be3d6"
    strings:
        $docopen = "<</CF<</StdCF<</AuthEvent/DocOpen/" ascii
        $ownerpass = /\/Filter\/Standard\/Length (40|128|256)\/O\(/
        $userpass = "/StmF/StdCF/StrF/StdCF/U(" ascii
        $perms = { 2f 50 65 72 6d 73 28 5b 07 ec 96 e8 68 ef 35 2e 75 02 16 0f 5c 5c 22 d1 29 }
    condition:
        uint32(0) == 0x46445025 and
        all of them
}


rule pdf_mal_script {
    strings:
        $magic = { 25 50 44 46 }
        $action0 = "<</S/Launch/Type/Action/Win<<" nocase ascii
        $action1 = "/Type/Action>>" nocase ascii
        $action2 = "/OpenAction" nocase ascii
        $action3 = "<< /Type /Action" nocase ascii
        $action4 = "/Type /Action" nocase ascii
        $uri = "/S /URI /Type /Action /URI"
        $launch = "/S /Launch /Win" nocase ascii
        $cmd = "(cmd.exe)" nocase ascii
        $ps = "powershell" nocase ascii
        $pscom0 = "DownloadFile" nocase ascii
        $pscom1 = "payload" nocase ascii
        $homepath = "%HOMEPATH%" nocase ascii
        $start0 = "start" nocase ascii
        $start1 = "startxref" nocase ascii
        $js0 = "<</S/JavaScript/JS" nocase ascii
        $js1 = /\/JS \([^)]+?\\/
        $js2 = "/JavaScript" nocase ascii
        $emb0 = "/EmbeddedFiles" nocase ascii
        $emb1 = "/EmbeddedFile" nocase ascii
        $url0 = "https://shapeupfitnessdkk-my.sharepoint.com/:b:/g/personal/michelle_shapeupfitness_dk/Ebd2GDh2N8JErL23JmMNmw8BQA7JVpGiS_C6TGkERpma4A?e=xBbtrV"
        $url1 = "https://ipfs.io/ipfs/QmSyYCjyTMyo1dM2dWBY6ExTmodmU1oSBWTdmEDTLrEenC#http://www.booking.com/"
        $url2 = "https://romacul.com.br/workshop/wp-content/mail.outlookoffice365.com.html"
        $url3 = "https://www.hitplus.fr/2018/click.php?url=https://cutt.ly/seU8MT6t#F8i_bfW"
        $url4 = "https://etehadshipping.com/"
        $url5 = "https://afarm.net/"
        $url6 = "https://portals.checkfedexexp.com"
        $url7 = "https://otcworldmedia.com"
        $url8 = "http://tiny.cc/"
        $url9 = "http://128.199.7.40/"
        $invoc = "%%Invocation:" nocase ascii
        $op0 = "-sOutputFile=" nocase ascii
        $op1 = "-dNumRenderingThreads=" nocase ascii
        $op2 = "-sDEVICE=" nocase ascii
        $op3 = "-dAutoRotatePages=" nocase ascii
        $script0 = "<script" nocase ascii
        $script1 = "</script>" nocase ascii
        $tag0 = "<event" nocase ascii
        $tag1 = "</event>" nocase ascii
        $event0 = "event.target.exportXFAData" nocase ascii
        $event1 = "activity=" nocase ascii
     condition:
        ($magic at 0 and (8 of them)) or
        ($magic at 0 and ($action0 or $action1 or $action2) and ($cmd or $ps) or ($pscom0 or $pscom1) and ($start0 or $start1) and $launch and $homepath and $js0) or
        ($magic at 0 and ($action2 or $action3) and (1 of ($emb*))) or
        ($magic at 0 and ( 1 of($url*))) or
        ($magic at 0 and $action4 and ($js1 or $js2)) or
        ($magic at 0 and $invoc and (2 of ($op*))) or
        ($magic at 0 and $uri) or
        ($magic at 0 and (2 of ($script*)) and ((2 of($event*)) and (2 of ($tag*))))
}


rule IconMismatch_PE_PDF {
    meta:
        description = "Icon mismatch: PE executable with PDF icons"
        author = "albertzsigovits"
    condition:
        uint16(0) == 0x5A4D
        and uint32(uint32(0x3C)) == 0x00004550
        and (
               hash.sha256(pe.resources[0].offset, pe.resources[0].length) == "0da488a59ce7c34b5362e2c3e900ebaa48c2fa182c183166d290c0c6f10f97c1" // PDF red icon #1
            or hash.sha256(pe.resources[0].offset, pe.resources[0].length) == "42cb714195c0255523313f41629c9d6a123d93f9789f8a8764e52cad405ea199" // PDF red icon #2
            or hash.sha256(pe.resources[0].offset, pe.resources[0].length) == "56cc2dea455f34271b031b51ff2b439a8a8083f4848b5308d4b42c827ba22c1f" // PDF red icon #3
            or hash.sha256(pe.resources[0].offset, pe.resources[0].length) == "683370eb202be9c57e6fe038e4a234c7a4e1f353dfbfe64d8f33397a5a0f0e81" // PDF red icon #4
            or hash.sha256(pe.resources[0].offset, pe.resources[0].length) == "68f1550f74d5cf2a52f1cf3780037facf60a6254e133fcc503a12e1ea5106184" // PDF red icon #5
            or hash.sha256(pe.resources[0].offset, pe.resources[0].length) == "9f12f3b8937665385f43f28caab2ded4469cefbec166d83e57d70e5a7b380067" // PDF red icon #6
            or hash.sha256(pe.resources[0].offset, pe.resources[0].length) == "a27b7e5c64c784418daa27bebb7ffcedbc919649d1a5b6446cd8c02516ba6da6" // PDF red icon #7
            or hash.sha256(pe.resources[0].offset, pe.resources[0].length) == "f7e6bb934282eae0225f37b2d05e81c7bfa95acbf11d1eb9c9662ed3accf5708" // PDF red icon #8
        )
}


rule PDF_Exploit_Enhanced {
    meta:
        description = "Detects common PDF exploits and embedded malware test files"
    strings:
        $aa = "/OpenAction"
        $acroform = "/AcroForm"
        $embedded_file = "/EmbeddedFile"
        $js = "/JS"
        $javascript = "/JavaScript"
        $launch = "/Launch"
        $eicar_pdf = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*" nocase
    condition:
        (any of ($js, $javascript, $aa, $acroform, $embedded_file, $launch) or $eicar_pdf)
}


rule SPICA__Strings {
    meta:
        author = "Google TAG"
        date = "2024-01-15"
        description = "Rust backdoor using websockets for c2 and embedded decoy PDF"
        hash = "37c52481711631a5c73a6341bd8bea302ad57f02199db7624b580058547fb5a9"
    strings:
        $s1 = "os_win.c:%d: (%lu) %s(%s) - %s"
        $s2 = "winWrite1"
        $s3 = "winWrite2"
        $s4 = "DNS resolution panicked"
        $s5 = "struct Dox"
        $s6 = "struct Telegram"
        $s8 = "struct Download"
        $s9 = "spica"
        $s10 = "Failed to open the subkey after setting the value."
        $s11 = "Card Holder: Bull Gayts"
        $s12 = "Card Number: 7/ 3310 0195 4865"
        $s13 = "CVV: 592"
        $s14 = "Card Expired: 03/28"

        $a0 = "agent\\src\\archive.rs"
        $a1 = "agent\\src\\main.rs"
        $a2 = "agent\\src\\utils.rs"
        $a3 = "agent\\src\\command\\dox.rs"
        $a4 = "agent\\src\\command\\shell.rs"
        $a5 = "agent\\src\\command\\telegram.rs"
        $a6 = "agent\\src\\command\\mod.rs"
        $a7 = "agent\\src\\command\\mod.rs"
        $a8 = "agent\\src\\command\\cookie\\mod.rs"
        $a9 = "agent\\src\\command\\cookie\\browser\\mod.rs"
        $a10 = "agent\\src\\command\\cookie\\browser\\browser_name.rs"
    condition:
        7 of ($s*) or 5 of ($a*)
}


rule G_Backdoor_TOUGHPROGRESS_LNK_1 {
    meta:
        author = "GTIG"
        date_created = "2025-04-29"
        date_modified = "2025-04-29"
        md5 = "65da1a9026cf171a5a7779bc5ee45fb1"
        rev = 1
    strings:
        $marker = { 4C 00 00 00 }
        $str1 = "rundll32.exe" ascii wide
        $str2 = ".\\image\\7.jpg,plus" wide
        $str3 = "%PDF-1"
        $str4 = "PYL="
    condition:
        $marker at 0 and all of them
}


rule LNK_Dropper_Russian_APT_Feb2024 {
    meta:
        Description = "Detects LNK dropper samples used by a Russian APT during a past campaign"
        Author = "RustyNoob619"
        Reference = "https://blog.cluster25.duskrise.com/2024/01/30/russian-apt-opposition"
        Hash = "114935488cc5f5d1664dbc4c305d97a7d356b0f6d823e282978792045f1c7ddb"
        SampleTesting = "Matches all five LNK Dropper Samples from the Blog"
    strings:
        $lnk = { 4C 00 00 00 01 14 02 00 }
        $pwrsh1 = "powershell.exe"
        $pwrsh2 = "WindowsPowerShell"
        $pwrsh3 = "powershell"
        $cmd = "cmd.exe"
        $ext1 = ".pdf.lnk"
        $ext2 = ".pdfx.lnk"
        $ext3 = "pdf.lnk" base64
        $scrpt1 = "Select-String -pattern \"JEVycm9yQWN0aW9uUH\" "
        $scrpt2 = "findstr /R 'JVBERi0xLjcNJeLjz9'" base64
        $blob1 = "$ErrorActionPreference = \"Continue\"" base64
        $blob2 = "$ProgressPreference = \"SilentlyContinue\"" base64
        $blob3 = "New-Alias -name pwn -Value iex -Force" base64
        $blob4 = "if ($pwd.path.toLower() -ne \"c:\\windows\\system32\")" base64
        $blob5 = "Copy-Item $env:tmp\\Temp.jpg $env:userprofile\\Temp.jpg" base64
        $blob6 = "attrib +h $env:userprofile\\Temp.jpg" base64
        $blob7 = "Start-Process $env:tmp\\Important.pdf" base64
        $net1 = "$userAgent = \"Mozilla/6.4 (Windows NT 11.1) Gecko/2010102 Firefox/99.0\"" base64
        $net2 = "$redirectors = \"6" base64
        $net3 = "$sleeps = 5" base64
        $http1 = "$request.Headers[\"X-Request-ID\"] = $request_token" base64
        $http2 = "$request.ContentType = \"application/x-www-form-urlencoded\"" base64
        $http3 = "$response1 = $(Send-HttpRequest \"$server/api/v1/Client/Info\" \"POST\" \"Info: $getenv64\")" base64
        $http4 = "$response = $($token = Send-HttpRequest \"$server/api/v1/Client/Token\" \"GET\")" base64
        $server1 = "$server = \"api-gate.xyz\"" base64
        $server2 = "$server = \"pdf-online.top\"" base64
        $unknown = "$server = " base64
    condition:
        $lnk at 0                       //LNK File Header
        and (any of ($pwrsh*) or $cmd) //searches for CMD or PowerShell execution
        and any of ($ext*)            //Fake Double Extension mimicing a PDF
        and any of ($scrpt*)         //Searches for a unique string to locate execution code
        and 5 of ($blob*)           //Base64 encoded execution blob
        and 2 of ($net*)
        and 3 of ($http*)
        and (any of ($server*) or $unknown) // C2 dommain config (Optional, can be removed)
}


private rule PDF_Structure
{
    meta:
        description = "Detects valid, readable PDF files"
        reference_files = "minimal.pdf (4a6f4ff8596321eea6fa482e7adbed01)"
        author = "ThreatFlux"
        date = "2024-12-31"
        version = "1.1"
        file_type = "PDF"
    strings:
        $header = "%PDF-"
        $eof_marker = "%%EOF"
        $startxref = "startxref"
        $xref = "xref"
        $trailer = "trailer"
    condition:
        // Header validation
        $header at 0 and
        uint8(5) >= 0x31 and          // Major version >= 1
        uint8(5) <= 0x37 and          // Major version <= 7
        uint8(7) == 0x2E and          // Decimal point
        uint8(8) >= 0x30 and          // Minor version >= 0
        uint8(8) <= 0x37 and          // Minor version <= 7
        // Basic structure requirements
        filesize > 32 and             // Minimum size for valid PDF
        $eof_marker in (filesize-10..filesize) and  // EOF marker near end
        // Required PDF elements
        $xref and                     // Must have cross-reference table
        $trailer and                  // Must have trailer
        $startxref and                // Must have startxref pointer
        // Basic binary check
        uint8(1) == 0x50 and         // 'P'
        uint8(2) == 0x44 and         // 'D'
        uint8(3) == 0x46             // 'F'
}


rule DETECT_CommandShell_PDF_Execution
{
    meta:
        description = "Detects Windows Command Shell execution artifacts in PDF files"
        author = "ThreatFlux"
        date = "2024-01-03"
        version = "2.1"
        // Classification
        threat_level = "Medium"
        category = "SUSPICIOUS_BEHAVIOR"
        malware_type = "PDF.CommandExecution"
        tlp = "WHITE"
        // MITRE ATT&CK Mapping
        mitre_attack = "T1059.003" // Windows Command Shell
        mitre_techniques = "T1204.002" // User Execution: Malicious File
        mitre_tactics = "Execution"
        // Detection Details
        detection_name = "PDF.Suspicious.CommandExecution"
        detection_rate = "Medium-High"
        false_positive_rate = "Medium"
        bypass_attempts = "String obfuscation, encoding variations"
        // File Characteristics
        file_type = "PDF"
        min_size = "1KB"
        max_size = "10MB"
        // References
        ref1 = "https://attack.mitre.org/techniques/T1059/003/"
        ref2 = "https://attack.mitre.org/techniques/T1204/002/"
        // Sample Metadata
        sample_hash1 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    strings:
        // Command Shell Artifacts
        $cmd1 = "cmd.exe" nocase ascii
        $cmd2 = "cmd /c" nocase ascii
        $cmd3 = "cmd /k" nocase ascii
        $cmd4 = "%comspec%" nocase ascii

        // Suspicious PDF Elements
        $suspc1 = "/JavaScript" ascii
        $suspc2 = "/OpenAction" ascii
        $suspc3 = "/Launch" ascii
    condition:
        PDF_Structure and
        (
            // Command Shell Reference
            any of ($cmd*) and
            // Supporting Suspicious Elements
            any of ($suspc*)
        )
}


rule apt_MuddyWater_malicious_pdf {
    meta:
        id = "77983aea-47cb-4436-b773-faf7be430339"
        version = "1.0"
        intrusion_set = "MuddyWater"
        description = "Detects malicious PDF used by MuddyWater"
        source = "Sekoia.io"
        creation_date = "2024-06-10"
        classification = "TLP:WHITE"
    strings:
        $ = "egnyte.com/fl/"
        $ = "/Type/Pages/Count 1"
    condition:
        uint32be(0) == 0x25504446 and
        filesize < 300KB and
        all of them
}


rule Bad_PDF {
    meta:
        description = "Detection patterns for the tool 'Bad-PDF' taken from the ThreatHunting-Keywords github project"
        author = "@mthcht"
        reference = "https://github.com/mthcht/ThreatHunting-Keywords"
        tool = "Bad-PDF"
        rule_category = "offensive_tool_keyword"
    strings:
        // Description: Bad-PDF create malicious PDF file to steal NTLM(NTLMv1/NTLMv2) Hashes from windows machines. it utilize vulnerability disclosed by checkpoint team to create the malicious PDF file. Bad-Pdf reads the NTLM hashes using Responder listener.
        // Reference: https://github.com/deepzec/Bad-Pdf
        $string1 = "Bad-Pdf" nocase ascii wide
    condition:
        any of them
}


rule DetectMaliciousScriptInPDF {
    meta:
        description = "Detects a PDF containing the text 'malicious_script'"
        author = "Kasthuri"
        date = "2024-09-28"
    strings:
        $eval = "eval("
        $js_function = "function("
        $malicious_js = "document.write(unescape("
    condition:
        $js_function or $eval or $malicious_js
}


rule DetectMaliciousURLs {
    meta:
        description = "Detects potentially malicious URLs in a PDF"
        author = "Kasthuri"
        date = "2024-09-28"
    strings:
        $phishing_url = /example\.com.*example\.com|example\.com.*secure|paypal\.com.*login/
        $url_shortener = /bit\.ly|tinyurl\.com|goo\.gl/
        $suspicious_extension = /\.exe|\.php\.exe|\.js\.exe/
        $redirect_chain = /redirect\?url=/
        $suspicious_path = /admin|config|login|wp-admin/
        // $obfuscated_url = /%[0-9A-Fa-f]{2}/
        // $base64_encoded_url = /[a-zA-Z0-9+\/=]{20,}/
    condition:
           $phishing_url
        or $url_shortener
        or $suspicious_extension
        or $redirect_chain
        or $suspicious_path
        // or $obfuscated_url
        // or $base64_encoded_url
}


rule MAL_DarkCloud_Phishing_PDF_IOC {
    meta:
        description = "Detects a specific malicious PDF file used in DarkCloud Stealer phishing campaigns based on its SHA256 hash."
        date = "2025-07-24"
        version = 1
        reference = "https://unit42.paloaltonetworks.com/darkcloud-stealer-and-obfuscated-autoit-scripting/"
        hash = "bf3b43f5e4398ac810f005200519e096349b2237587d920d3c9b83525bb6bafc"
        tags = "CRIME, INFOSTEALER, DARKCLOUD, FILE"
        mitre_attack = "T1566.001"
        malware_family = "DarkCloud"
        malware_type = "Infostealer"
    condition:
        // Match the specific SHA256 hash of the malicious PDF file.
        hash.sha256(0, filesize) == "bf3b43f5e4398ac810f005200519e096349b2237587d920d3c9b83525bb6bafc"
}


rule PDF_Javascript_Exploit {
    meta:
        description = "Detect potentially malicious PDF with JavaScript"
        author = "Cyberion Security"
        date = "2025-01-01"
        severity = "medium"
        category = "pdf"
    strings:
        $pdf = "%PDF"
        $js1 = "/JavaScript" nocase
        $js2 = "/JS" nocase
        $js3 = "eval(" nocase
        $js4 = "unescape(" nocase
    condition:
        $pdf at 0 and (1 of ($js*))
}


rule Trojan_Win32_Emotet_PDF_MTB{
    meta:
        description = "Trojan:Win32/Emotet.PDF!MTB,SIGNATURE_TYPE_PEHSTR_EXT,01 00 01 00 02 00 00 "
        reference = "https://github.com/roadwy/DefenderYara/blob/63fedb45b4243e50a3f85e9e4e3e45bb6f1a6b6f/Trojan/Win32/Poison/Trojan_Win32_Poison_EM_MTB.yara"
    strings:
        $a_02_0 = {0f b6 cb 03 c1 99 b9 ?? ?? ?? ?? f7 f9 8a 5d 00 8d 4c 24 ?? 8a 94 14 ?? ?? ?? ?? 32 da 88 5d 00 } //1
        $a_81_1 = {72 43 4a 67 43 63 58 4d 77 66 66 32 4f 32 32 57 54 32 7a 39 38 38 73 61 66 59 72 78 55 62 68 46 6f } //1 rCJgCcXMwff2O22WT2z988safYrxUbhFo
    condition:
        ((#a_02_0  & 1)*1+(#a_81_1  & 1)*1) >=1
}


rule Trojan_Win32_Poison_EM_MTB{
    meta:
        description = "Trojan:Win32/Poison.EM!MTB,SIGNATURE_TYPE_PEHSTR_EXT,05 00 05 00 05 00 00 "
        reference = "https://github.com/roadwy/DefenderYara/blob/63fedb45b4243e50a3f85e9e4e3e45bb6f1a6b6f/Trojan/Win32/Poison/Trojan_Win32_Poison_EM_MTB.yara"
    strings :
        $a_01_0 = {45 5a 45 4c 5c 6e 65 77 73 6c 65 74 74 65 72 5c 56 42 36 } //1 EZEL\newsletter\VB6
        $a_01_1 = {48 69 63 63 75 70 70 32 } //1 Hiccupp2
        $a_01_2 = {66 72 75 6d 70 36 } //1 frump6
        $a_01_3 = {6e 00 73 00 6c 00 74 00 2e 00 70 00 64 00 66 00 } //1 nslt.pdf
        $a_01_4 = {57 72 69 74 65 50 72 6f 63 65 73 73 4d 65 6d 6f 72 79 } //1 WriteProcessMemory
    condition:
        ((#a_01_0  & 1)*1+(#a_01_1  & 1)*1+(#a_01_2  & 1)*1+(#a_01_3  & 1)*1+(#a_01_4  & 1)*1) >=5
}


rule TrojanSpy_Win32_Shiotob_C{
    meta:
        description = "TrojanSpy:Win32/Shiotob.C,SIGNATURE_TYPE_PEHSTR_EXT,05 00 05 00 05 00 00 "
    strings :
        $a_01_0 = {5c 42 65 73 74 2e 70 64 66 } //1 \Best.pdf
        $a_01_1 = {68 00 74 00 74 00 70 00 3a 00 2f 00 2f 00 51 00 75 00 6f 00 74 00 69 00 65 00 } //1 http://Quotie
        $a_01_2 = {6d 00 65 00 61 00 73 00 75 00 72 00 2e 00 54 00 75 00 72 00 6e 00 } //1 measur.Turn
        $a_01_3 = {2e 00 53 00 69 00 6c 00 65 00 6e 00 74 00 } //1 .Silent
        $a_03_4 = {6a 00 6a 00 6a 01 6a 00 6a 02 68 00 00 00 40 8d 8d d8 fe ff ff 51 ff 15 ?? ?? ?? ?? 89 45 f0 8b 55 ec 83 ea 1b 81 fa d5 00 00 00 76 17 8b 45 ec 03 05 ?? ?? ?? ?? 0f b7 0d ?? ?? ?? ?? 03 c1 a3 ?? ?? ?? ?? 83 7d f0 ff 74 17 6a 01 6a 00 6a 00 8d 95 d8 fe ff ff 52 6a 00 6a 00 ff 15 } //2
    condition:
        ((#a_01_0  & 1)*1+(#a_01_1  & 1)*1+(#a_01_2  & 1)*1+(#a_01_3  & 1)*1+(#a_03_4  & 1)*2) >=5
}


rule Kimsuky_Lure_PDF  {
    meta:
        description = "Detection rule for a PDF file created by Kimsuky / APT43"
        author = "Alec Dhuse"
        creation_date = "2025-07-28"
        updated_date = "2025-07-28"
        date = "2025-07-28"
        in_the_wild = true
        threat_actor = "Kimsuky"
        hash = "ddf2832cde87548132688b28a27e6b4a0103e7d07fb88a5f10225145daa88926"
        rule_version = "1.0"
    strings:
        $re1 = /<<\s*\/Author\s*\(Raizo\)\s*\/Creator\s*\(þÿ\x00?M\x00?i\x00?c\x00?r\x00?o\x00?s\x00?o\x00?f\x00?t\x00?®\x00?\s+\x00?W\x00?o\x00?r\x00?d\x00?\s+\x00?2\x00?0\x00?1\x00?3\s*\)/
    condition:
        $re1
}


rule POTENTIAL_RU_APT_LNK_DEC23 {
    meta:
        author = "Ryan <@IntelCorgi>"
        date = "2024-03-20"
        description = "Decoy LNK drops HTTP shell and fake PDF. Attributed to unknown RU-nexus threat actor."
        source = "https://blog.cluster25.duskrise.com/2024/01/30/russian-apt-opposition"
    strings:
        $s0 = "CiRFcnJvckFjdGlvbl" ascii
        $s1 = "gci $env:tmp -Name Rar*" ascii wide
    condition:
            uint16(0) == 0x004c
        and filesize < 2MB
        and any of them
}


rule SUS_MSC_Icon_Pdf_Jan25 {
    meta:
        description = "Detects MSC with suspicious PDF icon observed in use by APT"
        note = "Categorising as SUS as unknown if this icon is unique to the actor or generic PDF stored in msc during build. Add other icon sizes for completeness."
        author = "Matt Green - @mgreen27"
        hash = "ca0dfda9a329f5729b3ca07c6578b3b6560e7cfaeff8d988d1fe8c9ca6896da5"
        date = "2025-01-16"
    strings:
        $xml = "<?xml"
        $pdf_console_file_icon_small = "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"
    condition:
        $xml at 0 and $pdf_console_file_icon_small
}


rule document_with_embedded_executable {
    meta:
        author = "Joaquin Villegas"
        description = "Detects documents with embedded executable content"
        category = "document"
        severity = "critical"
        date = "2025.07.15"
    strings:
        // Document headers
        $pdf_header = "%PDF-"
        // $ole_header = { D0 CF 11 E0 A1 B1 1A E1 }
        // $rtf_header = "{\\rtf"

        // Executable headers within document
        $pe_header = { 4D 5A }      // MZ header
        $elf_header = { 7F 45 4C 46 } // ELF header
        $macho_header = { FE ED FA CE } // Mach-O header

        // Embedded object indicators
        $embed1 = "\\objemb" nocase
        $embed2 = "/EmbeddedFile" nocase
        $embed3 = "Package" nocase
        $embed4 = "OLE Object" nocase

        // File streams
        $stream1 = "\\objdata" nocase
        $stream2 = "/F " nocase
        $stream3 = "/Type/EmbeddedFile" nocase
    condition:
            $pdf_header at 0
        and (any of ($pe_header, $elf_header, $macho_header))
        and (any of ($embed*) or any of ($stream*))
}


rule pdf_with_javascript {
    meta:
        author = "Joaquin Villegas"
        description = "Detects PDF files with embedded JavaScript and suspicious content"
        category = "document"
        severity = "medium"
        date = "2025.07.15"
    strings:
        // PDF header
        $pdf_header = "%PDF-"
        // JavaScript indicators
        $js1 = "/JavaScript" nocase
        $js2 = "/JS" nocase
        $js3 = "/OpenAction" nocase
        $js4 = "/AA" nocase
        // Suspicious JavaScript functions
        $js_func1 = "app.alert" nocase
        $js_func2 = "this.print" nocase
        $js_func3 = "app.launchURL" nocase
        $js_func4 = "this.submitForm" nocase
        $js_func5 = "app.response" nocase
        $js_func6 = "this.importDataObject" nocase
        // Exploit indicators
        $exploit1 = "unescape" nocase
        $exploit2 = "eval" nocase
        $exploit3 = "String.fromCharCode" nocase
        $exploit4 = "document.write" nocase
        // Heap spray indicators
        $heap1 = /\x90{10,}/  // NOP sled
        $heap2 = /%u9090/     // Unicode NOP
        $heap3 = /\x0c\x0c\x0c\x0c/  // Heap spray pattern
        // Form actions
        $form1 = "/F " nocase
        $form2 = "/Type/Action" nocase
        $form3 = "/S/SubmitForm" nocase
    condition:
        $pdf_header at 0 and
        (any of ($js*) or any of ($js_func*)) and
        (any of ($exploit*) or any of ($heap*) or any of ($form*))
}
