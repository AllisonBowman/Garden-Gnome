"""Resolving a citation to the Authority that published it.

CONTEXT.md draws the line: an Authority is the organisation, a Citation is the
document. Tier attaches to the organisation, so NC State is tier 2 whichever
factsheet a claim happens to land on — and precedence in resolve.py is only
meaningful once every citation from one body agrees on who that body is.

Resolution is by domain, not by the `source` title. Titles are prose written
per citation: Clemson appears under seventeen of them in the tranche. A domain
is canonical.
"""
import pytest

from app.data.claims.authorities import authority_for, licence_of


def test_one_body_writing_under_many_titles_is_still_one_authority():
    a = authority_for("https://plants.ces.ncsu.edu/plants/monstera-deliciosa/",
                      "NC State Extension Gardener Plant Toolbox")
    b = authority_for("https://plants.ces.ncsu.edu/plants/ficus-lyrata/",
                      "NC State Extension Plant Toolbox")

    assert a == b
    assert a.name == "NC State Extension"


def test_one_body_publishing_on_two_domains_is_still_one_authority():
    # Missouri Botanical Garden serves Plant Finder from both.
    a = authority_for("https://plantfinder.mobot.org/x", "Plant Finder")
    b = authority_for("https://www.missouribotanicalgarden.org/y", "Plant Finder")

    assert a == b
    assert a.name == "Missouri Botanical Garden"


def test_the_url_decides_when_the_title_credits_two_bodies():
    # One tranche citation is titled "NC State Extension Plant Toolbox /
    # Clemson HGIC ...". The page it links to is Clemson's, so it is Clemson's
    # claim — a title match would have filed it under the wrong body.
    resolved = authority_for(
        "https://hgic.clemson.edu/factsheet/indoor-plants",
        "NC State Extension Plant Toolbox / Clemson HGIC Indoor Plants")

    assert resolved.name == "Clemson Cooperative Extension"


def test_extension_services_and_botanic_gardens_share_a_tier():
    # We have no principled basis for ranking one extension service above
    # another, so they sit at the same tier and same-tier disagreements are
    # settled by resolve.py's deterministic tie-break rather than by a
    # pecking order we invented.
    names = ["https://plants.ces.ncsu.edu/a", "https://hgic.clemson.edu/b",
             "https://www.rhs.org.uk/c", "https://plantfinder.mobot.org/d"]

    assert {authority_for(u, "").tier for u in names} == {2}


def test_an_unknown_publisher_is_refused_rather_than_guessed():
    # A domain nobody has vetted has no tier and no licence, so admitting it
    # would put an unweighted claim into precedence and an unaudited source
    # into the catalog.
    assert authority_for("https://some-plant-blog.example/post", "A Blog") is None


@pytest.mark.parametrize("url", ["", "not-a-url", None])
def test_a_citation_with_no_usable_url_is_refused(url):
    assert authority_for(url, "NC State Extension Plant Toolbox") is None


def test_every_authority_carries_a_licence_on_the_record():
    # ADR 0001: withdrawing a source has to be a query, which means the terms
    # we accepted it under must be stored rather than remembered.
    for url in ["https://plants.ces.ncsu.edu/a", "https://www.rhs.org.uk/c"]:
        assert licence_of(authority_for(url, "").name)


def test_an_unregistered_name_has_no_licence_to_report():
    assert licence_of("A Plant Blog") == ""


def test_usda_plants_resolves_at_tier_one():
    # 17 U.S.C. § 105 -- a federal work, public domain, no copyright to
    # attribute-and-not-redistribute the way the extension services need.
    # It joins WFO/WCVP as the open bulk-taxonomic tier the module docstring
    # has reserved since the registry was first built.
    a = authority_for("https://plants.usda.gov/plant-profile/MODE", "")
    assert a.name == "USDA PLANTS Database"
    assert a.tier == 1


def test_usda_plants_and_its_redirect_domain_are_one_authority():
    # plants.usda.gov 301s to plants.sc.egov.usda.gov, and a citation could
    # carry either -- they must not become two rows for the same publisher.
    a = authority_for("https://plants.usda.gov/plant-profile/MODE", "")
    b = authority_for(
        "https://plants.sc.egov.usda.gov/plant-profile/MODE", "")
    assert a == b


def test_usda_plants_may_only_claim_hardiness_zones():
    # It was investigated and rejected as a houseplant-care source: it does
    # not track most of the catalog's species, and where it does, its
    # Characteristics schema measures rangeland establishment, not potted
    # care. It earns tier 1 for names and zones only -- not a blank cheque
    # to outrank Clemson on humidity because a URL happened to resolve.
    from app.data.claims.authorities import authority_may_claim
    assert authority_may_claim("USDA PLANTS Database", "hardiness_zones")
    assert not authority_may_claim("USDA PLANTS Database", "humidity_need")
    assert not authority_may_claim("USDA PLANTS Database", "toxic_to_pets")


def test_an_unrestricted_authority_may_claim_anything():
    # The extension services stay the general care-data basis -- registering
    # a scoped authority must not narrow the ones that already exist.
    from app.data.claims.authorities import authority_may_claim
    assert authority_may_claim("NC State Extension", "humidity_need")
    assert authority_may_claim("NC State Extension", "hardiness_zones")


def test_usda_plants_carries_a_public_domain_licence():
    assert "public domain" in licence_of("USDA PLANTS Database").lower()
