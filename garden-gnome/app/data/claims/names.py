"""One spelling rule for a botanical name, shared by everything that keys one.

A hybrid is written "Genus × epithet" with U+00D7 MULTIPLICATION SIGN, and the
sources write one such name three ways: "Nepeta × faassenii", the spaceless
"Nepeta ×faassenii", and an ASCII "Nepeta x faassenii". A nothogenus carries the
marker in front ("× Fatshedera lizei", the corpus's "x Cuprocyparis leylandii").
Every one of those is one name, and this module is the only place that says so.
Four private copies of the rule -- the sync's, the pre-landing dedup's, the
corpus invariant's and the expansion guard's -- is what let one hybrid key two
ways at once, so the copies now all call in here.

  canonical()  the spelling this catalog stores: marker spaced, whitespace collapsed.
  key()        the matching key: canonical, marker folded to "x", case-folded.
  words()      the name's words with the marker set aside, so a shape check can
               count "Genus × epithet" as the two-word binomial it is.

The marker is a token in a key, never deleted: "Citrus × aurantiifolia" and
"Citrus aurantiifolia" stay different keys. Folding them together would be a
guess that a nothospecies and a same-epithet species are one plant, and which
plant the evidence describes is the one thing this catalog never guesses at.
What `key` does fold is the three *spellings* of one marker.

Only U+00D7 is respaced. An ASCII "x" counts as a marker only where it already
stands alone as a word, so "Solanum xanti" and "Xanthosoma sagittifolium" keep
their epithets whole.
"""
import re

#: U+00D7 MULTIPLICATION SIGN -- the hybrid marker, never the letter x.
MARKER = "×"

_MARKER_SPACING = re.compile(r"\s*" + MARKER + r"\s*")
_WHITESPACE = re.compile(r"\s+")


def canonical(name: str | None) -> str:
    """The stored spelling. 'Nepeta ×faassenii' -> 'Nepeta × faassenii'."""
    spaced = _MARKER_SPACING.sub(" " + MARKER + " ", name or "")
    return _WHITESPACE.sub(" ", spaced).strip()


def key(name: str | None) -> str:
    """One key for the spellings of one name.

    'Abelia × grandiflora', 'Abelia ×grandiflora', 'Abelia x grandiflora' and
    'Abelia  X grandiflora' -> 'abelia x grandiflora'.
    """
    return canonical(name).replace(MARKER, "x").casefold()


def words(name: str | None) -> list[str]:
    """The name's words, hybrid marker dropped.

    'Chrysanthemum × morifolium' and 'Chrysanthemum ×morifolium' -> two words,
    the same as an ordinary binomial; '× Fatshedera' -> one, still a bare genus.
    An author abbreviation or a cultivar tail is a word and still counts.
    """
    return [w for w in canonical(name).split()
            if w != MARKER and w.casefold() != "x"]


def genus_token(name: str | None) -> str:
    """The genus word of a name, marker excluded. '× Fatshedera lizei' -> 'Fatshedera'."""
    found = words(name)
    return found[0] if found else ""
