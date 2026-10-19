"""b124_qcheck.py URL QUOTE [QUOTE...] -- b124-only strict quote check (b119_qcheck.py plus a rendered-body check).

For each quote: verify_quotes' own present() verdict; strict = a newline-stacked quote is a run of CONSECUTIVE text
nodes (one-line quote inside a single node); body = the same strict test against rendered <body> data nodes only, so
text that exists only in <title> or in alt/title attributes (tooltips) fails it. Uses verify_quotes' fetch+extract
path; reads the shared cache, never edits it. Run from garden-gnome/ with .venv/bin/python. Quotes may use the two
characters backslash-n for a newline.
"""
import re
import sys

sys.path.insert(0, 'scripts/catalog')
import verify_quotes as vq  # noqa: E402


class _Body(vq._Text):
    """Rendered data nodes only: no alt/title attribute text."""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP_TAGS or a.get("aria-hidden") == "true" or a.get("hidden") is not None:
            if tag not in vq.VOID:
                self._skip_stack.append(tag)


def _clean(parts):
    return [re.sub(r'\s+', ' ', x).strip() for x in parts if x.strip()]


def nodes(raw):
    p = vq._Text()
    p.feed(raw)
    return _clean(p.parts)


def body_nodes(raw):
    m = re.search(r'<body\b', raw, re.I)
    p = _Body()
    p.feed(raw[m.start():] if m else raw)
    return _clean(p.parts)


def strict(q, ns):
    lines = [re.sub(r'\s+', ' ', x).strip() for x in q.split('\n')]
    if len(lines) == 1:
        return any(lines[0] in n for n in ns)
    for i in range(len(ns) - len(lines) + 1):
        if ns[i:i + len(lines)] == lines:
            return True
    return False


def main():
    url = sys.argv[1]
    status, raw = vq.fetch(url)
    print('## fetch status:', status)
    if not raw:
        sys.exit(1)
    text = vq.norm(vq.extract(raw))
    ns, bs = nodes(raw), body_nodes(raw)
    for q in sys.argv[2:]:
        q = q.replace('\\n', '\n')
        print(f"present={vq.present(q, text)} strict={strict(q, ns)} body={strict(q, bs)} :: {q[:100]!r}")


if __name__ == '__main__':
    main()
