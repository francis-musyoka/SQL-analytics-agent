from src import context


def test_short_text_is_unchanged():
    assert context.truncate_result("hello") == "hello"


def test_long_text_is_truncated_with_marker():
    text = "x" * 5000
    out = context.truncate_result(text)
    assert len(out) < len(text)
    assert "truncated" in out
