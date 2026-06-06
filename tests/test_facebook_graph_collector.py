from app.collectors.facebook_graph_collector import _parse_facebook_datetime, _summary_count


def test_facebook_summary_count_reads_graph_api_shape():
    assert _summary_count({"summary": {"total_count": 12}}) == 12
    assert _summary_count(None) == 0


def test_facebook_datetime_parser_handles_zulu_time():
    parsed = _parse_facebook_datetime("2026-06-06T01:02:03+0000")
    assert parsed is not None
    assert parsed.year == 2026
