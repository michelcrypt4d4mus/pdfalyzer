
rule PDF_with_XORed_JS_keywords
{
    meta:
        author             = "Michel de Cryptadamus"
        description        = "Look for Javascript keywords with XOR"
        created_date       = "2022-10-01"
        updated_date       = "2022-10-01"
	strings:
        $this = "this\\s*" xor
        $require = "require" xor
		$const = "const" xor
        $eval = "eval" xor
	condition:
        $this or $require or $const or $eval
}



// rule Frontslash_regex
// {
//     meta:
//         author             = "Michel de Cryptadamus"
//         description        = "Find patterns that look like an embedded regex"
//         created_date       = "2022-10-01"
//         updated_date       = "2022-10-01"
// 	strings:
//         $front_slashes = /\/.*?\//
// 	condition:
//         $front_slashes
// }
