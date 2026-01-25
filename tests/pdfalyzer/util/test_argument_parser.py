from pdfalyzer.util.argument_parser import parse_arguments


def test_parse_arguments(pdfalyze_analyzing_malicious_args):
    parse_arguments(pdfalyze_analyzing_malicious_args)
