rule PDFalyzer_test_suite
{
   meta:
        description = "PDFalyzer test suite"
   strings:
        $reg0 = /special types of PostScript files/
   condition:
        $reg0
}
