"""Resolution rules: Claims in, Resolved values out.

The vocabulary is CONTEXT.md's — Claim, Authority, Authority tier, Resolved
value, Material disagreement, Genus-inferred, Harm-capable field. The
decisions being enforced are ADR 0001 (values are derived from claims, never
typed in) and ADR 0002 (inference stops at the genus; toxicity never inherits).

Pure logic: no database, no ORM. A Claim here is a plain record, so these
rules stay testable without a migration and can't drift toward persistence
concerns.
"""
from app.data.claims.resolve import Authority, Claim, resolve


WFO = Authority(name="World Flora Online", tier=1)
NC_STATE = Authority(name="NC State Extension", tier=2)
CLEMSON = Authority(name="Clemson HGIC", tier=2)
WIKIPEDIA = Authority(name="Wikipedia", tier=3)


def claim(field, value, *, subject="Dracaena trifasciata", authority=NC_STATE):
    return Claim(subject=subject, field=field, value=value, authority=authority)


def test_a_single_claim_becomes_the_resolved_value():
    result = resolve("Dracaena trifasciata", [claim("humidity_need", "low")])

    assert result.values["humidity_need"] == "low"
    assert result.provenance["humidity_need"] == "sourced"
    assert result.refusals == []


def test_the_better_authority_wins_an_ordinary_disagreement():
    # Tier 1 outranks tier 3. Order of arrival must not matter, so the same
    # pair is resolved both ways round.
    claims = [claim("soil_ph_min", 6.5, authority=WIKIPEDIA),
              claim("soil_ph_min", 5.5, authority=WFO)]

    assert resolve("Dracaena trifasciata", claims).values["soil_ph_min"] == 5.5
    assert resolve(
        "Dracaena trifasciata", list(reversed(claims))
    ).values["soil_ph_min"] == 5.5


def test_two_equal_authorities_are_broken_deterministically():
    # Same tier, ordinary imprecision. Which one wins matters less than that
    # the answer never depends on the order claims happened to arrive in —
    # otherwise re-running the resolver silently rewrites the catalog.
    claims = [claim("soil_ph_min", 6.0, authority=NC_STATE),
              claim("soil_ph_min", 5.5, authority=CLEMSON)]

    forwards = resolve("Dracaena trifasciata", claims)
    backwards = resolve("Dracaena trifasciata", list(reversed(claims)))

    assert forwards.values == backwards.values


def test_a_harm_capable_field_refuses_rather_than_picking_a_winner():
    # 50F and 32F are not imprecision about the same fact, they are two
    # different claims about when this plant is damaged by cold. Preferring
    # the better-ranked authority here would ship a number that the other
    # source says is wrong by enough to kill the plant.
    result = resolve("Dracaena trifasciata", [
        claim("chill_damage_f", 50, authority=NC_STATE),
        claim("chill_damage_f", 32, authority=WFO),
    ])

    assert "chill_damage_f" not in result.values
    assert [r.field for r in result.refusals] == ["chill_damage_f"]


def test_an_ordinary_field_still_resolves_when_sources_are_far_apart():
    # The same spread on a field that cannot hurt anything is just the
    # documented disagreement between extension services — take the better
    # authority and move on.
    result = resolve("Dracaena trifasciata", [
        claim("light_fc_min", 100, authority=NC_STATE),
        claim("light_fc_min", 800, authority=WFO),
    ])

    assert result.values["light_fc_min"] == 800
    assert result.refusals == []


def test_a_gap_is_filled_from_the_genus_and_says_so():
    # Clemson's light table classifies whole genera, so a genus-level claim is
    # a real thing a source said — not a guess. It still may not masquerade as
    # a measurement of this species.
    result = resolve("Dracaena trifasciata", [
        claim("humidity_need", "low"),
        claim("light_fc_min", 100, subject="Dracaena"),
    ])

    assert result.values["light_fc_min"] == 100
    assert result.provenance["light_fc_min"] == "genus_inferred"
    assert result.provenance["humidity_need"] == "sourced"


def test_the_species_outranks_its_genus_even_from_a_worse_authority():
    # Specificity beats authority tier here: a tier-3 source that looked at
    # this species knows more about it than a tier-1 source describing the
    # genus in general.
    result = resolve("Dracaena trifasciata", [
        claim("light_fc_min", 250, authority=WIKIPEDIA),
        claim("light_fc_min", 100, subject="Dracaena", authority=WFO),
    ])

    assert result.values["light_fc_min"] == 250
    assert result.provenance["light_fc_min"] == "sourced"


def test_inference_stops_at_the_genus_and_never_reaches_the_family():
    # ADR 0002. A family-level claim is not evidence about a species.
    result = resolve("Dracaena trifasciata", [
        claim("light_fc_min", 100, subject="Asparagaceae"),
    ])

    assert "light_fc_min" not in result.values


def test_toxicity_never_inherits_in_either_direction():
    # ADR 0002. A genus-inferred "non-toxic" is an invented safety verdict,
    # and a genus-inferred "toxic" libels a safe plant into being avoided.
    # Neither is something a source said about this species.
    safe_genus = resolve("Dracaena trifasciata", [
        claim("toxic_to_pets", False, subject="Dracaena")])
    toxic_genus = resolve("Dracaena trifasciata", [
        claim("toxic_to_pets", True, subject="Dracaena")])

    assert "toxic_to_pets" not in safe_genus.values
    assert "toxic_to_pets" not in toxic_genus.values


def test_withdrawing_an_authority_re_derives_rather_than_leaving_a_stale_value():
    # Resolved values are derived from the claims that exist right now
    # (ADR 0001), so losing an authority to a licence problem must move the
    # value, not leave the old one sitting there sourced to nothing. The
    # database-level half of this — recompute leaving no stale rows — is a
    # separate cycle at the persistence seam.
    all_claims = [claim("soil_ph_min", 5.5, authority=WFO),
                  claim("soil_ph_min", 6.5, authority=NC_STATE)]
    assert resolve("Dracaena trifasciata", all_claims).values["soil_ph_min"] == 5.5

    surviving = [c for c in all_claims if c.authority != WFO]
    assert resolve("Dracaena trifasciata", surviving).values["soil_ph_min"] == 6.5

    assert "soil_ph_min" not in resolve("Dracaena trifasciata", []).values
