rule PDFalyzer_test_suite
{
   meta:
        description = "PDFalyzer test suite"
   strings:
        $reg0 = "Roman" ascii nocase
   condition:
        $reg0
}
