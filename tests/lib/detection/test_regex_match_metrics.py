from pdfalyzer.detection.regex_match_metrics import RegexMatchMetrics


def test_matches_too_big_or_small_calculation():
    metrics = RegexMatchMetrics()
    metrics.skipped_matches_lengths[0] = 5
    metrics.skipped_matches_lengths[1] = 10
    metrics.skipped_matches_lengths[2] = 20

    assert metrics.num_matches_skipped_for_being_empty() == 5
    assert metrics.num_matches_skipped_for_being_too_big() == 30
