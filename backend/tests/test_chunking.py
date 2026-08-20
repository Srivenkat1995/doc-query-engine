from app.chunking import chunk_text


def test_chunking_is_line_aware_and_stable() -> None:
    text = "First line\nSecond line\n\nThird line"

    first = chunk_text(text, max_chars=100)
    second = chunk_text(text, max_chars=100)

    assert [chunk.content for chunk in first] == [
        "First line\nSecond line\nThird line"
    ]
    assert first == second
    assert len(first[0].content_hash) == 64


def test_chunking_splits_long_source_without_empty_chunks() -> None:
    chunks = chunk_text("one\ntwo\nthree\nfour", max_chars=7)

    assert [chunk.position for chunk in chunks] == [0, 1, 2]
    assert all(chunk.content for chunk in chunks)