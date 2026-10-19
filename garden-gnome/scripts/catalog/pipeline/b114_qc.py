"""b114_qc.py URL [-g REGEX ...] [QUOTE ...] -- b114-only page reader and strict quote check.

-g REGEX prints the rendered text nodes around each node matching REGEX (node list from verify_quotes' own parser).
Any other argument is a quote: prints verify_quotes' present() verdict plus a strict check that a one-line quote
sits inside one rendered node, and a newline-stacked quote is a run of consecutive nodes. Quotes may use the two
characters backslash-n for a newline. Reads the shared cache through vq.fetch; never edits it.
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
    return any(ns[i:i + len(lines)] == lines for i in range(len(ns) - len(lines) + 1))


def main():
    url, args = sys.argv[1], sys.argv[2:]
    status, raw = vq.fetch(url)
    print('## fetch status:', status)
    if not raw:
        sys.exit(1)
    text = vq.norm(vq.extract(raw))
    ns = nodes(raw)
    i = 0
    while i < len(args):
        if args[i] == '-g':
            pat = args[i + 1]
            i += 2
            hits = [k for k, n in enumerate(ns) if re.search(pat, n, re.I)]
            print(f'## {pat!r}: {len(hits)} node hit(s)')
            for k in hits[:6]:
                print('   ' + ' ¦ '.join(ns[max(0, k - 2):k + 9])[:700])
            continue
        q = args[i].replace('\\n', '\n')
        i += 1
        print(f"present={vq.present(q, text)} strict={strict(q, ns)} :: {q[:110]!r}")


if __name__ == '__main__':
    main()
