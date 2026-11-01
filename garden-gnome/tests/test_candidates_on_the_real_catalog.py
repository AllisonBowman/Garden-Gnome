"""Who the candidate list may put forward, judged on the catalog that ships.

A fixture can say a rule is right; only the real tranche says which plants it
lets through. Commit 798f905 kept food crops NC State rates highly on the
list by exempting anything recorded as eaten, and Mayapple -- eaten for its
ripe fruit, highly poisonous everywhere else -- walked back on with them. So
this module seeds a scratch database the way a cold start does (app.data.seed,
then the claim sync over every verified batch) and pins, by name, which
high-severity plants the crop exception admits.
"""
import itertools
import shutil
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, delete, select

from app.models.models import (
    Authority, CareLog, CareSchedule, Claim, GrowingArea, Plant, Species,
    SpeciesTrait, SyncState,
)
from app.services import fit
from app.services.toxicity import is_food_crop, never_put_forward, safety_of

#: The crops NC State rates a high-severity poison for people that still
#: belong on a vegetable bed's list. A new name here is a product decision.
CROPS = {
    "Solanum tuberosum", "Solanum melongena", "Arachis hypogaea",
    "Physalis philadelphica", "Phaseolus lunatus",
}
#: Recorded as eaten, and never put forward: Mayapple is rated high by NC
#: State with only its ripe fruit eaten; the two Asian wisterias are tagged
#: invasive species on NC State's own pages.
NEVER = {"Podophyllum peltatum", "Wisteria floribunda", "Wisteria sinensis"}
#: Kept off every list by a source's own listing, read from every vetted
#: citation about the species and not only the safety ones (tranche.
#: WEED_FIELD, ADR 0011): the phrase "invasive species" or "noxious weed" in
#: a quote about this plant. Before that read, only the five whose tag sat
#: under the pet flag's citation were caught. A new name here is a data
#: change; a missing one means a record lost its citation. Canna indica is
#: here on a sentence calling it an invasive species in Australia, which the
#: rule reads like any other listing; narrowing that is a product decision.
WEEDS = {
    "Berberis bealei", "Buddleja davidii", "Canna indica", "Hedera helix",
    "Ligustrum japonicum", "Miscanthus sinensis", "Nandina domestica",
    "Perilla frutescens", "Solanum dulcamara", "Tradescantia fluminensis",
    "Wisteria floribunda", "Wisteria sinensis",
    "Pistia stratiotes", "Pyrus calleryana",
}


@pytest.fixture(scope="module")
def catalog(migrated_db_url, tmp_path_factory):
    """The shipped catalog in a private database: seed, then claim sync."""
    from app.data import seed as seed_module
    from app.data.claims.sync import sync_catalog

    work = tmp_path_factory.mktemp("real") / "catalog.db"
    shutil.copy(Path(migrated_db_url.removeprefix("sqlite:///")), work)
    engine = create_engine(f"sqlite:///{work.as_posix()}")
    with Session(engine) as s:
        # Whatever other tests left in the shared database, gone.
        for model in (Claim, Authority, CareLog, CareSchedule, SpeciesTrait,
                      Plant, Species, SyncState):
            s.exec(delete(model))
        s.commit()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(seed_module, "engine", engine)
        mp.setattr(seed_module, "run_migrations", lambda: None)
        seed_module.seed()
    with Session(engine) as s:
        report = sync_catalog(s)
        assert not report.skipped
    session = Session(engine)
    yield session
    session.close()
    engine.dispose()


def _species(session) -> dict[str, Species]:
    return {sp.scientific_name: sp for sp in session.exec(select(Species)).all()}


def _beds(goals):
    for sun, surface in itertools.product(
            ["full_sun", "partial_sun", "shade"],
            ["in_ground_bed", "raised_bed", "containers"]):
        yield GrowingArea(name="bed", temp_exposure="outdoor", shelter="exposed",
                          sun_exposure=sun, surface=surface, goals=goals)


def _candidate_names(session, area) -> set[str]:
    return {c.species.scientific_name
            for c in fit.candidates(session.exec(select(Species)).all(), area)}


def test_the_crop_exception_admits_exactly_the_five_crops(catalog):
    """Across the whole tranche: every species a source rates high or fatal
    for people that is still allowed on a list is one of the five crops."""
    admitted = set()
    for name, sp in _species(catalog).items():
        safety = safety_of(sp)
        if never_put_forward(safety.toxicity, safety.evidence) \
                and not fit.never_a_candidate(sp):
            admitted.add(name)
    assert admitted == CROPS


@pytest.mark.parametrize("goals", [None, ["edible"]])
def test_crops_stay_and_mayapple_and_wisteria_stay_out_whatever_the_goals(
        catalog, goals):
    """The exception does not read the bed's goals: a bed that asked for
    nothing gets the crops too, and one that asked for food does not get
    Mayapple back."""
    offered: set[str] = set()
    for area in _beds(goals):
        offered |= _candidate_names(catalog, area)
    assert CROPS <= offered, CROPS - offered
    assert not NEVER & offered, NEVER & offered


def test_mayapple_is_recorded_as_eaten_and_still_ruled_out(catalog):
    mayapple = _species(catalog)["Podophyllum peltatum"]
    assert mayapple.is_edible is True
    assert not is_food_crop(mayapple.scientific_name)
    assert fit.never_a_candidate(mayapple)


def test_taro_is_not_a_crop_the_exception_knows_and_is_rated_medium(catalog):
    """Taro (Colocasia esculenta) is eaten only cooked ("Poisonous until
    cooked") and the exception does not know it as a crop, so a high rating
    would take it off the list. NC State rates it Medium, the same as
    tomato, so the high-severity rule does not reach it: it is offered with
    its hazard line and its edibility note, like tomato."""
    taro = _species(catalog)["Colocasia esculenta"]
    safety = safety_of(taro)
    assert not is_food_crop(taro.scientific_name)
    assert safety.evidence.edibility_conditional
    assert safety.evidence.rating == "medium"
    assert not never_put_forward(safety.toxicity, safety.evidence)


def test_a_weed_listing_on_any_cited_field_keeps_exactly_these_off_every_list(catalog):
    """Across the whole tranche: the species a vetted source lists as an
    invasive species or a noxious weed, on whatever field the citation was
    filed under, and none of them is ever put forward."""
    listed = set()
    for name, sp in _species(catalog).items():
        safety = safety_of(sp)
        if safety.evidence.invasive or safety.evidence.noxious:
            listed.add(name)
            assert fit.never_a_candidate(sp), name
    assert listed == WEEDS, listed ^ WEEDS
    offered: set[str] = set()
    for area in _beds(None):
        offered |= _candidate_names(catalog, area)
    assert not WEEDS & offered, WEEDS & offered
