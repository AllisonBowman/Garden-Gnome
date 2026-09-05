"""Writing the verified tranche into the catalog as evidence.

This is a writer, so it follows the same rules plan 3.1 imposed on
`apply_review`: it refuses what it cannot account for, it can be re-run without
doubling anything, and `--dry-run` leaves the database exactly as it found it.
"""
import json

import pytest
from sqlmodel import select

from app.data.claims.ingest import ingest_records
from app.models.models import Authority, Claim

NCSU_URL = "https://plants.ces.ncsu.edu/plants/dracaena-trifasciata/"

RECORD = {
    "common_name": "Snake Plant",
    "scientific_name_accepted": "Dracaena trifasciata",
    "humidity_need": "low",
    "light_fc_min": 100,
    "toxic_to_pets": True,
    "citations": [
        {"claim": "humidity_need low; light_fc_min 100; toxic_to_pets true",
         "source": "NC State Extension Gardener Plant Toolbox",
         "url": NCSU_URL, "quote": "Tolerates low humidity"},
    ],
}


@pytest.fixture(autouse=True)
def empty_evidence(session):
    for model in (Claim, Authority):
        for row in session.exec(select(model)).all():
            session.delete(row)
    session.commit()
    yield


def stored_claims(session):
    return session.exec(select(Claim)).all()


def test_ingesting_a_record_stores_its_claims_and_their_publisher(session):
    report = ingest_records(session, [RECORD])

    claims = stored_claims(session)
    assert {c.field for c in claims} == {
        "humidity_need", "light_fc_min", "toxic_to_pets"}
    assert report.claims_written == 3

    # Types survive: the value is JSON, not str().
    by_field = {c.field: json.loads(c.value_json) for c in claims}
    assert by_field["light_fc_min"] == 100
    assert by_field["toxic_to_pets"] is True

    authority = session.exec(select(Authority)).one()
    assert authority.name == "NC State Extension"
    assert authority.tier == 2
    # ADR 0001 -- the terms we accepted a source under are stored, not recalled.
    assert authority.licence


def test_the_quote_is_stored_even_though_it_is_never_shipped(session):
    ingest_records(session, [RECORD])

    assert all(c.quote for c in stored_claims(session))


def test_running_it_twice_does_not_double_the_evidence(session):
    first = ingest_records(session, [RECORD])
    second = ingest_records(session, [RECORD])

    assert first.claims_written == 3
    assert second.claims_written == 0
    assert second.claims_already_present == 3
    assert len(stored_claims(session)) == 3
    # And the publisher is not re-created either.
    assert len(session.exec(select(Authority)).all()) == 1


def test_a_value_without_vetted_support_is_reported_and_not_written(session):
    # `soil_base` has a value but no citation naming it; the blog citation is
    # from a publisher with no tier and no licence, so it supports nothing.
    record = dict(RECORD, soil_base="standard_potting", humidity_pct_min=40,
                  citations=RECORD["citations"] + [
                      {"claim": "humidity_pct_min 40", "source": "A Blog",
                       "url": "https://some-plant-blog.example/x",
                       "quote": "about 40%"}])

    report = ingest_records(session, [record])

    assert set(report.unsupported["Dracaena trifasciata"]) == {
        "soil_base", "humidity_pct_min"}
    assert {c.field for c in stored_claims(session)} == {
        "humidity_need", "light_fc_min", "toxic_to_pets"}


def test_dry_run_leaves_the_database_exactly_as_it_found_it(session):
    report = ingest_records(session, [RECORD], dry_run=True)

    # It still reports what it *would* have done, which is the point of it.
    assert report.claims_written == 3
    assert stored_claims(session) == []
    assert session.exec(select(Authority)).all() == []


def test_the_whole_verified_tranche_lands_and_resolves(session):
    """End to end: every curated species in the catalog is now cited evidence."""
    from app.data.claims.ingest import ingest_tranche
    from app.data.claims.store import resolve_from_db

    report = ingest_tranche(session)

    # 349 (b1-b5) + 81 (b6) + 42 (b7) + 41 (b8) + 54 (b9) + 47 (b10) + 51
    # (b11) + 39 (b12) + 35 (b13) + 34 (b14) + 37 (b15) + 34 (b16) + 24
    # (b17) + 5 (b18) + 41 (b19) + 42 (b20) + 59 (b21) + 28 (b22) + 42 (b23)
    # + 50 (b24) + 46 (b25) + 37 (b26) + 32 (b27) + 34 (b28) + 35 (b29) + 39
    # (b30) + 34 (b31) + 42 (b32) + 38 (b33) + 34 (b34) + 40 (b35) + 51 (b36)
    # + 42 (b37) + 39 (b38) + 38 (b39) + 65 (b40) + 36 (b41) + 43 (b42)
    # + 78 (b43) + 76 (b44) + 72 (b45) - 1 (b14's Common Morning Glory
    # soil_drainage, nulled 2026-09-02 when a corpus-wide quote check found
    # its only citation quoted NC State drainage tags the page does not
    # carry) + 65 (b46) + 39 (b47) + 27 (b48) + 27 (b49) + 27 (b50)
    # + 27 (b51) = 2297. + 25 (b52) = 2322. + 27 (b53) = 2349. + 23 (b54) = 2372. + 20 (b55) = 2392. + 24 (b56) = 2416. + 21 (b57) = 2437. + 18 (b58) = 2455. + 17 (b59) = 2472. + 27 (b60) = 2499. + 21 (b61) = 2520. + 23 (b62) = 2543. + 25 (b63) = 2568. + 22 (b64) = 2590. + 27 (b65) = 2617. + 24 (b66) = 2641. b18 was the
    # last batch of the original 129-curated-species collection run.
    # b19-b34 are batches of a follow-on "blind spots" pass -- species
    # chosen by direct inspection of coverage gaps (b19: no true lilies --
    # the single highest-priority pet-safety gap in the catalog, lily
    # kidney failure in cats -- no azalea, oleander, sago palm, hydrangea;
    # b20: rose, tulip, daffodil, poinsettia, cyclamen), then by
    # cross-referencing every species researched against anchors in the
    # app's own code: sample.py::TOP_HOUSEPLANTS (b21 -- African Violet,
    # Schefflera, and String of Pearls turned out to already be covered
    # under reclassified taxonomic names and were dropped before landing),
    # toxicity.py::AROID_GENERA (b22, one representative species per
    # uncovered genus), and toxicity.py::SPECIES_SPECIFIC_RISK (b23 --
    # Hemerocallis/Daylily shares true lilies' severe cat-specific
    # kidney-failure pattern and was a real gap), plus more species
    # confirmed missing by direct grep (b23 tail, b24-b34 -- b24 introduced
    # this catalog's first large landscape trees; b25 added more
    # trees/shrubs plus the first tree-form fruit crops, apple and fig;
    # b26 added three more severe safety gaps -- castor bean, lily of the
    # valley, English yew -- plus more trees; b27 added more toxic bulbs --
    # hyacinth, amaryllis, angel's trumpet -- the true Crocus as a
    # deliberate companion to Autumn Crocus/Colchicum, and this catalog's
    # first true aquatic pond plant; b28 added American Holly plus more
    # fruit/nut trees and two new ornamental categories, grasses and
    # groundcovers; b29 added three more severe safety gaps -- mistletoe,
    # monkshood, common milkweed -- plus this catalog's first hemiparasitic
    # species and more trees; b30 added poison ivy -- the first plant
    # landed with a contact-dermatitis rather than ingestion hazard --
    # plus pokeweed and more vines/trees; b31 added avocado and jimsonweed,
    # a deliberate companion to Angel's Trumpet already in the catalog,
    # plus more trees and houseplants; b32 added a common indoor tree, a
    # cactus, a toxic native wildflower, and more shrubs, the first batch
    # built to explicitly guard against b31's non-cat/dog toxicity-scope
    # defect; b33 added belladonna and bittersweet nightshade, plus a
    # second hydrangea and dogwood species as deliberate companions to ones
    # already in the catalog; b34 added poison hemlock plus deliberate
    # companion species for hibiscus, magnolia, and citrus already in the
    # catalog; b35 added Ginkgo, Nandina, Bougainvillea, Purple Passionflower,
    # Buttercup, a third Hydrangea species (Climbing Hydrangea) as a deliberate
    # companion to the two already in the catalog, Crown of Thorns, and
    # Lantana; b36 added Bleeding Heart, Japanese Barberry, Weigela, Arrowwood
    # Viburnum, a deliberate two-species Jasmine companion test (Jasminum
    # officinale vs. Trachelospermum jasminoides), Bearded Iris, and
    # Gladiolus; b37 added Sweetgum, Butterfly Bush, Coral Bells, Russian Sage
    # (resolved to its reclassified accepted name Salvia yangii), Astilbe,
    # Blue False Indigo, Lenten Rose, and Bugleweed; b38 added Virginia
    # Creeper (a deliberate identification-confusion companion to Poison
    # Ivy), American Beech, Eastern Cottonwood, and five common Southern
    # landscape shrubs -- Red Tip Photinia, Chinese Fringe Flower, Tea Olive,
    # Japanese Pittosporum, Thorny Elaeagnus; b39 added Cherry Laurel, a
    # deliberate Cotoneaster/Firethorn identification-confusion companion
    # pair, Red-twig Dogwood/Tatarian Dogwood (a companion to the tree-form
    # dogwoods already covered), St. John's Wort, Virginia Sweetspire,
    # Summersweet, and Dwarf Fothergilla; b40 added Gasteria bicolor, a
    # Gesneriad houseplant cluster (Florist's Gloxinia, Lipstick Plant,
    # Goldfish Plant), Stromanthe sanguinea (a companion to Calathea and
    # Maranta already covered, resolved to its reclassified name Stromanthe
    # thalia), and three common annuals -- Edging Lobelia, Flowering Tobacco,
    # Wishbone Flower; b41 added five ornamental grasses (Maiden Grass,
    # Switchgrass, Pink Muhly Grass, Japanese Sedge, Blue Fescue), Hardy Ice
    # Plant, Moss Phlox (a companion to the taller border Phlox already
    # covered), and Rose Moss; b42 added three privacy-hedge conifers
    # (American Arborvitae, Leyland Cypress -- resolved to its reclassified
    # name x Hesperotropsis leylandii, Eastern Redcedar), Slender Deutzia
    # (corrected to Japanese Snow Flower), Glossy Abelia, and two more
    # deliberate companion species -- Tea Plant vs. Camellia japonica, Star
    # Magnolia vs. Saucer/Southern Magnolia; b43 added Elephant Bush (checked
    # against Jade Plant already covered), a fern cluster (Bird's Nest Fern,
    # Rabbit's Foot Fern, Autumn Fern), three toxic caudiciform/succulent
    # species (Firestick, Desert Rose, Madagascar Palm), and Umbrella Plant;
    # b44 added three houseplant palms (Lady Palm, Pygmy Date Palm, Cat
    # Palm), Watermelon Peperomia (a companion to Peperomia obtusifolia),
    # Dwarf Banana, Freesia, and two epiphytic cacti -- Orchid Cactus and
    # Mistletoe Cactus -- the first batch landed through the corpus-wide
    # invariant test and the mechanical citation verifier; b45 added four
    # fruit crops (Pomegranate, Olive, Kiwifruit, Blackberry -- a companion
    # to Red Raspberry), Sweetheart Hoya (a companion to Hoya carnosa), and
    # the first carnivorous-plant cluster -- Purple Pitcher Plant, Winged
    # Tropical Pitcher Plant, Cape Sundew; b46 -- the first batch researched
    # on Sonnet and audited on Opus -- added Tarragon, Fennel, Sacred Lotus,
    # Satin Pothos, Monstera adansonii (landed as Swiss Cheese Vine after
    # the audit caught the sibling species' name), Pineapple, Papaya, and
    # Apricot; b47 -- the first six-species overnight batch -- added a
    # shade-shrub set: Winter Daphne, Japanese Pieris, Oregon Grape,
    # Japanese Aucuba, Japanese Aralia, and Japanese Skimmia; b48 added two
    # Ilex companions to American Holly (Japanese Holly, Yaupon Holly),
    # Sasanqua Camellia, Red-osier Dogwood, Fragrant Water Lily, and
    # Doghobble; b49 added Japanese Persimmon (a companion to American
    # Persimmon), White Mulberry, Mandarin Orange (a third Citrus), Bee
    # Balm, Canada Goldenrod, and New England Aster; b50 added a native
    # woodland set: Foamflower, Canadian Wild Ginger, Solomon's Seal,
    # Virginia Bluebells, Lady Fern, and Northern Sea Oats; b51 added a
    # second woodland set: Mayapple, Black Cohosh, Great White Trillium,
    # Wild Geranium, Woodland Phlox, and Eastern Bluestar -- its verify
    # stage hit a usage limit mid-run and was finished by a resume; b52
    # added a third woodland set: Goat's Beard, Fringed Bleeding Heart
    # (named to avoid colliding with b36's Bleeding Heart), Dwarf Crested
    # Iris, Cinnamon Fern, Goldenseal, and Blue Cohosh -- its verify stage
    # died on a DNS outage and was finished by a resume; b53 added native
    # woodland and wet-meadow perennials: Large-flowered Bellwort,
    # Celandine Poppy, Golden Ragwort, White Turtlehead, Cardinal Flower,
    # and Joe Pye Weed -- the last renamed at landing from an alphabetized
    # list's first entry to MoBot's designated name; b54 added native
    # meadow perennials: New York Ironweed, Oxeye Sunflower, Swamp
    # Milkweed, Obedient Plant, Queen of the Prairie, and Early
    # Meadow-rue -- two drainage tokens moved from wet to moderate on the
    # sources' own cultivation statements; b55 added a second meadow set:
    # Golden Alexanders, Wild Senna, Cup Plant, Cutleaf Coneflower,
    # Sneezeweed, and False Aster -- Sneezeweed's NC State Poison block is
    # an open follow-up, flagged in its toxicity_detail; b56 added a third
    # meadow set: Golden Crown (Anacis tripteris, the 2024 placement NC
    # State carries), Blunt Mountain Mint, Wild Bergamot, Grey-head
    # Coneflower, Pale Purple Coneflower, and Arkansas Bluestar -- three
    # common names changed at landing on the lead-name rule; b57, after
    # the loop resumed, added native prairie species: Indian Grass, Little
    # Bluestem, Rattlesnake Master, Purple Prairie Clover, White False
    # Indigo, and Rough Goldenrod; b58 added a second prairie set: Big
    # Bluestem, Sideoats Grama, Wild Quinine, Canada Anemone, Prairie
    # Smoke, and Purple Poppy Mallow -- its verify stage stalled on API
    # 529s for four attempts and finished on a user-directed resume; b59
    # added a third prairie set: Lead Plant, New Jersey Tea, Royal
    # Catchfly, Nodding Onion, Smooth Aster, and Rough Blazing Star -- two
    # audits died on a DNS outage and a resume finished them; b60 added
    # native shrubs: Black Chokeberry, Buttonbush, Spicebush, Winterberry,
    # Steeplebush, and Shrubby St. John's Wort; b61 added a second shrub
    # set: Ninebark, Fragrant Sumac, American Hazelnut, Sweet Fern, Bush
    # Honeysuckle, and Lowbush Blueberry; b62 added a third shrub set:
    # Common Witch Hazel, Mountain Laurel, Shadblow Serviceberry, Northern
    # Bayberry, Blackhaw Viburnum, and Pinxterbloom Azalea; b63 added
    # native trees: Sassafras, Black Gum, Sourwood, American Hornbeam,
    # Fringe Tree, and Pawpaw; b64 added a second tree set: American
    # Hophornbeam, American Linden, Common Hackberry, Sweetbay Magnolia,
    # Carolina Silverbell, and American Yellowwood; b65 a third native tree
    # set -- Ohio Buckeye, Red Buckeye, Honey Locust, Shagbark Hickory,
    # Black Cherry, and Green Hawthorn -- landed after a weekly usage-limit
    # stall and a plain resume two days later; b66 a fourth native tree set --
    # American Bladdernut, Hoptree, Green Ash, Black Locust, Slippery Elm, and
    # Red Mulberry). Every
    # batch was re-verified against the strict loader before landing here
    # -- see each batch's own normalizations entry for what, if anything,
    # that pass caught.
    assert report.claims_written == 2641
    # Still 8, not 9 -- ask.ifas.ufl.edu resolves to the same "UF/IFAS
    # Extension" authority name as edis.ifas.ufl.edu, and _authority_row
    # mints rows by name, so it reuses the existing row rather than
    # creating a second one for the same organisation.
    assert len(session.exec(select(Authority)).all()) == 8

    # A species picked out of the batch resolves to its researched values,
    # each carrying the citation it came from.
    snake = resolve_from_db(session, "Dracaena trifasciata")
    assert snake.values["humidity_need"] == "low"
    assert snake.values["water_regime"] == "dry_thoroughly_between"
    assert snake.values["toxic_to_pets"] is True
    assert snake.provenance["humidity_need"] == "sourced"


def test_two_stored_sources_disagreeing_on_cold_tolerance_refuse(session):
    """The refusal path works on stored evidence, not just in the pure layer.

    Resolving the real tranche produces no refusals, which is a fact about the
    data rather than proof the guard is connected. This wires two genuinely
    conflicting claims through the database to show it is.
    """
    from app.data.claims.store import resolve_from_db

    conflicting = {
        "scientific_name_accepted": "Testus conflictus",
        "chill_damage_f": 50,
        "citations": [
            {"claim": "chill_damage_f 50", "source": "NC State",
             "url": "https://plants.ces.ncsu.edu/testus/", "quote": "below 50"},
            {"claim": "chill_damage_f 32", "source": "Clemson",
             "url": "https://hgic.clemson.edu/testus/", "quote": "below 32"},
        ],
    }
    ingest_records(session, [conflicting])
    # The second citation asserts a different value for the same field; store
    # it directly, since one record can only carry one value per field.
    clemson = session.exec(
        select(Authority).where(Authority.name == "Clemson Cooperative Extension")
    ).first()
    if clemson is None:
        clemson = Authority(name="Clemson Cooperative Extension", tier=2)
        session.add(clemson)
        session.commit()
        session.refresh(clemson)
    session.add(Claim(
        subject="Testus conflictus", field="chill_damage_f", value_json="32",
        authority_id=clemson.id, citation_url="https://hgic.clemson.edu/testus/",
        citation_title="Clemson", quote="below 32"))
    session.commit()

    result = resolve_from_db(session, "Testus conflictus")

    assert "chill_damage_f" not in result.values
    assert [r.field for r in result.refusals] == ["chill_damage_f"]
