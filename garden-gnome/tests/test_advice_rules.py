"""The rule-based advice keeps the rules the reminders keep.

The app's reminder engine (mobile notifications/plan.ts) refuses to suggest
misting, which the extension services say does nothing or harm, and refuses
to suggest feeding from November to February. The rule-based advice is read
beside those reminders, so it must not tell someone to do what the reminders
refuse to. It also speaks of checks, never chores: a schedule says when to
look, and the plant decides.
"""
from datetime import datetime, timedelta

import pytest

from app.models.models import CareLog, CareSchedule, CareType, MaturityStage, Plant, Species
from app.services import advisor
from app.services.advisor import _advise_stub, _build_prompt


def make_species(**kw):
    base = dict(common_name="Test Fern", scientific_name="Testus fernus",
                toxic_to_pets=None)
    base.update(kw)
    return Species(**base)


def make_plant():
    return Plant(nickname="Lily", species_id=1, maturity_stage=MaturityStage.mature)


def schedule(care_type, low, high):
    return CareSchedule(species_id=1, care_type=care_type,
                        interval_days_min=low, interval_days_max=high)


def logged(care_type, days_ago):
    return CareLog(plant_id=1, action=care_type,
                   logged_at=datetime.utcnow() - timedelta(days=days_ago))


@pytest.fixture()
def month(monkeypatch):
    """Set the month the advice is given in."""
    def set_month(m):
        monkeypatch.setattr(advisor, "_this_month", lambda: m)
    set_month(6)
    return set_month


# --- misting -------------------------------------------------------------------

def test_misting_is_never_recommended(month):
    out = _advise_stub(make_species(), make_plant(), [],
                       [schedule(CareType.water, 7, 10), schedule(CareType.mist, 1, 2)])
    assert "Misting" not in out and "💨" not in out
    assert "Watering" in out


def test_a_species_whose_only_schedule_is_misting_reads_as_scheduled_not_blank(month):
    out = _advise_stub(make_species(), make_plant(), [],
                       [schedule(CareType.mist, 1, 2)])
    assert "Misting" not in out
    assert "No check schedule is on record" not in out


# --- feeding ---------------------------------------------------------------------

@pytest.mark.parametrize("m", [11, 12, 1, 2])
def test_no_feeding_in_the_resting_season(month, m):
    month(m)
    out = _advise_stub(make_species(), make_plant(), [logged(CareType.fertilize, 90)],
                       [schedule(CareType.fertilize, 30, 60)])
    assert out == "🌿 Fertilizing: resting season, so hold off feeding until March."


def test_feeding_follows_the_species_own_months(month):
    month(3)
    sp = make_species(fertilize_active_months=[5, 6, 7])
    out = _advise_stub(sp, make_plant(), [], [schedule(CareType.fertilize, 30, 60)])
    assert out == "🌿 Fertilizing: resting season, so hold off feeding until May."
    month(6)
    out = _advise_stub(sp, make_plant(), [], [schedule(CareType.fertilize, 30, 60)])
    assert out.startswith("🌿 Fertilizing: no log yet")


def test_a_cited_winter_month_is_still_outside_what_the_reminders_allow(month):
    month(2)
    sp = make_species(fertilize_active_months=[2, 3, 4])
    out = _advise_stub(sp, make_plant(), [], [schedule(CareType.fertilize, 30, 60)])
    assert "hold off feeding until March" in out


# --- checks, not chores -------------------------------------------------------------

def test_no_log_yet_asks_for_a_check_not_an_action(month):
    out = _advise_stub(make_species(), make_plant(), [], [schedule(CareType.water, 7, 10)])
    assert out == ("💧 Watering: no log yet — its schedule puts this every 7–10 "
                   "days; check before you do anything.")
    assert "recommended" not in out


def test_before_the_window_the_plant_still_decides(month):
    out = _advise_stub(make_species(), make_plant(), [logged(CareType.water, 2)],
                       [schedule(CareType.water, 7, 10)])
    assert out == ("💧 Watering: logged 2 days ago. Next check in 5 days; act "
                   "sooner only if the plant shows it needs it.")
    assert "hold off" not in out


def test_inside_the_window_it_is_a_check(month):
    out = _advise_stub(make_species(), make_plant(), [logged(CareType.water, 8)],
                       [schedule(CareType.water, 7, 10)])
    assert out == ("💧 Watering: logged 8 days ago, inside the 7–10 day window. "
                   "Check, and act only if it's needed.")


def test_past_the_window_is_worth_a_check_not_due(month):
    out = _advise_stub(make_species(), make_plant(), [logged(CareType.water, 14)],
                       [schedule(CareType.water, 7, 10)])
    assert out == ("💧 Watering: logged 14 days ago — past the 10 day mark, "
                   "worth a check today.")
    assert "Likely due" not in out


def test_one_day_is_singular(month):
    out = _advise_stub(make_species(), make_plant(), [logged(CareType.water, 6)],
                       [schedule(CareType.water, 7, 10)])
    assert "Next check in 1 day;" in out


# --- toxicity -------------------------------------------------------------------------

def test_the_toxicity_line_names_people_when_a_source_does(month):
    sp = make_species(toxic_to_pets=True,
                      toxicity_detail="NC State rates poison severity Medium.")
    out = _advise_stub(sp, make_plant(), [], [schedule(CareType.water, 7, 10)])
    line = out.splitlines()[-1]
    assert line.startswith("⚠️ Toxic to pets and people.")
    assert "NC State Extension rates its poison severity for people medium." in line


def test_no_toxicity_line_without_a_recorded_hazard(month):
    out = _advise_stub(make_species(), make_plant(), [], [schedule(CareType.water, 7, 10)])
    assert "⚠️" not in out


def test_a_hazard_to_people_alone_is_still_said(month):
    """Poison ivy: non-toxic to pets per NC State, a high-severity hazard to
    people. The old line keyed on the pet flag and said nothing."""
    sp = make_species(common_name="Poison Ivy", scientific_name="Toxicodendron radicans",
                      toxic_to_pets=False,
                      toxicity_detail="NC State Extension rates human Poison Severity as \"High\".")
    out = _advise_stub(sp, make_plant(), [], [])
    assert "⚠️ Seriously toxic to people." in out


# --- the weather label ------------------------------------------------------------------

def test_the_prompt_names_no_weather_provider():
    """Whichever of three providers answered, the prompt must not tell a model
    it was Apple Weather; the client shows the real credit."""
    from app.models.models import GrowingArea, Shelter, SunExposure, TempExposure
    area = GrowingArea(name="Balcony", shelter=Shelter.exposed,
                       temp_exposure=TempExposure.outdoor,
                       sun_exposure=SunExposure.full_sun)
    prompt = _build_prompt(make_species(), make_plant(), [], [], "", area,
                           {"current": {"temp_f": 70}, "daily": []})
    assert "LOCAL WEATHER (authoritative current conditions and forecast):" in prompt
    assert "Apple" not in prompt
