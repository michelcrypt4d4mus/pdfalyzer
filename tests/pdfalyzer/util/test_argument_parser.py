from pdfalyzer.util.argument_parser import parse_arguments


def test_parse_arguments(export_analyzing_malicious_args):
    parse_arguments(export_analyzing_malicious_args)
