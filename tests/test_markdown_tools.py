import json

from src.tools.markdown_tools import render_structured_result


def test_snippet_mode_basic():
    sample = {'structuredContent': {'result': 'This is a <b>test</b> snippet.\n\nSecond paragraph.'}}
    res = render_structured_result(sample, {'mode': 'snippet', 'max_tokens': 200})
    assert res.get('mode') == 'snippet'
    assert 'markdown' in res
    assert isinstance(res['markdown'], str)
    # chars field should match the markdown length
    assert res.get('chars') == len(res['markdown'])
    assert 'test' in res['markdown'].lower()


def test_chunked_mode_paragraph_splitting():
    # Build multiple paragraphs so the chunker will produce multiple chunks
    paras = [f"Paragraph {i}: " + ("lorem ipsum " * 10).strip() for i in range(8)]
    text = "\n\n".join(paras)
    sample = {'structuredContent': {'result': text}}
    res = render_structured_result(sample, {'mode': 'chunked', 'max_tokens': 300})
    assert res.get('mode') == 'chunked'
    chunks = res.get('chunks')
    assert isinstance(chunks, list)
    assert len(chunks) >= 2
    # Each chunk should include markdown text and accurate chars count
    for c in chunks:
        assert 'markdown' in c
        assert c.get('chars') == len(c['markdown'])
        assert c['markdown'].strip()
