from typing import Dict, List, Generator, Any
import re

try:
    import html2text
    _HAS_HTML2TEXT = True
except Exception:
    _HAS_HTML2TEXT = False


def _looks_like_html(s: str) -> bool:
    if not s:
        return False
    low = s.lower()
    return any(tag in low for tag in ("<html", "<body", "<div", "<p", "<br"))


def _html_to_text(s: str) -> str:
    if _HAS_HTML2TEXT:
        try:
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.body_width = 0
            return h.handle(s)
        except Exception:
            pass
    # Fallback: very small heuristic stripper
    return re.sub(r"<[^>]+>", "", s)


def _paragraph_chunks(text: str, target_chars: int) -> Generator[str, None, None]:
    """Yield chunks of approximately target_chars length by joining paragraphs.

    Splits on double-newline boundaries and accumulates paragraphs until the
    chunk would exceed target_chars, then yields the chunk and continues.
    """
    if not text:
        return
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paras:
        yield text[:target_chars]
        return

    current: List[str] = []
    cur_len = 0
    for p in paras:
        plen = len(p) + 2  # account for the paragraph separator when joined
        if cur_len + plen > target_chars and current:
            yield "\n\n".join(current)
            current = [p]
            cur_len = plen
        else:
            current.append(p)
            cur_len += plen

    if current:
        yield "\n\n".join(current)


def render_structured_result(structured: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """Render a structured result (from EDGAR or other tools) into markdown.

    Args:
        structured: A dict containing the retrieval result. Expected keys include
            - 'result' or 'structuredContent' or similar; fallback to raw structured.
        options: Dict of options. Supported keys:
            - mode: 'snippet' (default) or 'chunked'
            - max_tokens: integer target (approximate)
            - snippet_key: path/key inside structured that contains the snippet(s)

    Returns:
        A dict with either {'mode':'snippet','markdown':...} or
        {'mode':'chunked','chunks':[{'index':0,'markdown':..., 'meta':...}, ...]}
    """
    mode = (options or {}).get('mode', 'snippet')
    max_tokens = int((options or {}).get('max_tokens', 1200) or 1200)
    # Very rough token->char heuristic
    max_chars = max(256, max_tokens * 4)

    # Try to locate snippet/text content inside the structured object
    snippets: List[Dict[str, Any]] = []

    # Common locations
    if isinstance(structured, dict):
        # If the tool produced 'structuredContent' with 'result' text
        if 'structuredContent' in structured and isinstance(structured['structuredContent'], dict):
            sc = structured['structuredContent']
            # Some tools put the printable text under 'result'
            if 'result' in sc and isinstance(sc['result'], str):
                snippets.append({'text': sc['result'], 'meta': {}})
        # If there is a top-level 'content' with list of blocks
        if 'content' in structured and isinstance(structured['content'], list):
            for block in structured['content']:
                if isinstance(block, dict) and block.get('type') == 'text' and isinstance(block.get('text'), str):
                    snippets.append({'text': block['text'], 'meta': {}})
        # A generic 'result' key
        if 'result' in structured and isinstance(structured['result'], str):
            snippets.append({'text': structured['result'], 'meta': {}})
        # 'structured' or 'data' with nested result lists
        for k in ('structured', 'data', 'structuredContent', 'structured_result'):
            if k in structured and isinstance(structured[k], (str, list, dict)):
                v = structured[k]
                if isinstance(v, str):
                    snippets.append({'text': v, 'meta': {}})
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            text = item.get('snippet') or item.get('text') or item.get('body')
                            meta = {kk: item.get(kk) for kk in ('date', 'accession', 'url') if kk in item}
                            if text:
                                snippets.append({'text': text, 'meta': meta})
                        elif isinstance(item, str):
                            snippets.append({'text': item, 'meta': {}})
                elif isinstance(v, dict):
                    t = v.get('snippet') or v.get('text') or v.get('result')
                    if isinstance(t, str):
                        snippets.append({'text': t, 'meta': {}})

    # If nothing found, attempt a naive string conversion
    if not snippets:
        try:
            text = str(structured)
            snippets.append({'text': text, 'meta': {}})
        except Exception:
            snippets = []

    # Normalize: convert HTML when needed
    for s in snippets:
        t = s.get('text') or ''
        if _looks_like_html(t):
            s['text'] = _html_to_text(t)

    # Build markdown according to mode
    if mode == 'snippet':
        # Combine snippets into a single markdown string up to max_chars
        out_parts: List[str] = []
        cur_len = 0
        for s in snippets:
            piece = ''
            meta = s.get('meta', {}) or {}
            # Add metadata header if present
            if meta:
                meta_lines = [f"- {k}: {v}" for k, v in meta.items()]
                piece += "\n" + "\n".join(meta_lines) + "\n\n"
            piece += s.get('text', '')
            if cur_len + len(piece) > max_chars and cur_len > 0:
                break
            out_parts.append(piece)
            cur_len += len(piece)

        md = "\n\n---\n\n".join(out_parts).strip()
        if not md:
            md = "(no text available)"
        return {'mode': 'snippet', 'markdown': md, 'chars': len(md)}

    # chunked mode: produce paragraph-based chunks of approx max_chars
    chunks: List[Dict[str, Any]] = []
    combined_text = "\n\n".join(s.get('text', '') for s in snippets if s.get('text'))
    if not combined_text:
        return {'mode': 'chunked', 'chunks': []}

    for idx, chunk in enumerate(_paragraph_chunks(combined_text, max_chars)):
        chunks.append({'index': idx, 'markdown': chunk, 'chars': len(chunk)})

    return {'mode': 'chunked', 'chunks': chunks}
