"""b107_qcheck.py URL QUOTE [QUOTE...] -- b107-only strict quote check.

For each quote: verify_quotes' own present() verdict, plus a strict check that a newline-stacked quote is a run of
CONSECUTIVE rendered text nodes (each line == one stripped node, in order, nothing between) and that a one-line quote
lies inside a single rendered node. Uses verify_quotes' fetch+extract path; reads the shared cache, never edits it.
Run from garden-gnome/ with .venv/bin/python. Quotes may use the two characters backslash-n for a newline.
"""
import re
import sys

sys.path.insert(0, 'scripts/catalog')
import verify_quotes as vq  # noqa: E402


def nodes(raw):
    p = vq._Text()
    p.feed(raw)
    return [re.sub(r'\s+', ' ', x).strip() for x in p.parts if x.strip()]


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
    ns = nodes(raw)
    for q in sys.argv[2:]:
        q = q.replace('\\n', '\n')
        print(f"present={vq.present(q, text)} strict={strict(q, ns)} :: {q[:100]!r}")


if __name__ == '__main__':
    main()
