"""Turn Claims into Resolved values.

Pure: no session, no engine, no SQLModel. The catalog's tables adapt to this
module rather than the other way round, so the rules that decide what the app
is willing to assert stay testable without a database.

See CONTEXT.md for the vocabulary and ADR 0001/0002 for why resolution works
this way.
"""
from dataclasses import dataclass, field as dc_field
from typing import Any


@dataclass(frozen=True)
class Authority:
    """An organisation whose publications count as evidence."""
    name: str
    tier: int


@dataclass(frozen=True)
class Claim:
    """One field's value for one subject, as asserted by one authority.

    `subject` is what the claim is *about* — a binomial for a species-level
    claim, a bare genus name for a genus-level one.
    """
    subject: str
    field: str
    value: Any
    authority: Authority


@dataclass(frozen=True)
class Refusal:
    """A field the resolver declined to assert, and why."""
    field: str
    reason: str


@dataclass
class Resolution:
    values: dict[str, Any] = dc_field(default_factory=dict)
    provenance: dict[str, str] = dc_field(default_factory=dict)
    refusals: list[Refusal] = dc_field(default_factory=list)


# Fields where a wrong value injures an animal or kills a plant. These never
# resolve through a Material disagreement — see CONTEXT.md and ADR 0002.
HARM_CAPABLE = frozenset({"toxic_to_pets", "chill_damage_f", "water_regime"})

# How far two claims about the same field may sit apart before the difference
# stops being imprecision and becomes a genuine conflict. Fields absent here
# are categorical: any difference at all is material.
TOLERANCE: dict[str, float] = {
    "chill_damage_f": 5,
}

# Fields that may never be borrowed from the genus, in either direction. A
# genus-inferred "non-toxic" is an invented safety verdict and a genus-inferred
# "toxic" libels a safe plant; neither is something a source said about this
# species. Coverage here grows only by citation. See ADR 0002.
NEVER_INHERIT = frozenset({"toxic_to_pets"})


def _is_material(field: str, values: list[Any]) -> bool:
    distinct = {str(v) for v in values}
    if len(distinct) <= 1:
        return False
    numeric = [v for v in values if isinstance(v, (int, float))
               and not isinstance(v, bool)]
    if len(numeric) == len(values) and field in TOLERANCE:
        return (max(numeric) - min(numeric)) > TOLERANCE[field]
    return True


def genus_of(binomial: str) -> str:
    """The genus part of a scientific name. 'Dracaena trifasciata' -> 'Dracaena'."""
    return binomial.split()[0] if binomial else ""


def resolve(subject: str, claims) -> Resolution:
    """Reconcile every Claim about `subject` into one value per field.

    Claims about the species itself are used first. Gaps may then be filled
    from claims about its genus, marked `genus_inferred`. Claims about
    anything else — a family, an unrelated species — are ignored outright:
    that is how ADR 0002's "inference stops at the genus" is enforced, by
    never admitting the evidence rather than by filtering it later.
    """
    genus = genus_of(subject)
    species_claims = [c for c in claims if c.subject == subject]
    genus_claims = [c for c in claims if c.subject == genus and c.subject != subject]

    result = _resolve_scope(species_claims, "sourced")
    inherited = _resolve_scope(genus_claims, "genus_inferred")

    settled = set(result.values) | {r.field for r in result.refusals}
    for field, value in inherited.values.items():
        if field in settled or field in NEVER_INHERIT:
            continue  # the species spoke for itself, or we already refused
        result.values[field] = value
        result.provenance[field] = inherited.provenance[field]
    return result


def _resolve_scope(claims, provenance: str) -> Resolution:
    by_field: dict[str, list[Claim]] = {}
    for claim in claims:
        by_field.setdefault(claim.field, []).append(claim)

    result = Resolution()
    for field, field_claims in by_field.items():
        if field in HARM_CAPABLE and _is_material(
                field, [c.value for c in field_claims]):
            # Deliberately assert nothing. A better-ranked authority is not
            # evidence that the other one is wrong, and on these fields being
            # confidently wrong is the expensive outcome.
            result.refusals.append(Refusal(
                field=field,
                reason="sources disagree materially on a harm-capable field",
            ))
            continue
        # Tier first. Ties break on authority name, then on the value itself,
        # so the winner never depends on the order claims arrived in — a
        # re-run must not quietly rewrite the catalog.
        winner = min(field_claims, key=lambda c: (
            c.authority.tier, c.authority.name, str(c.value)))
        result.values[field] = winner.value
        result.provenance[field] = provenance
    return result
