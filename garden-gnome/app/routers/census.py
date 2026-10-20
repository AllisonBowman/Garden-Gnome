"""Census router — anonymized aggregate views of plant data.

Privacy model (decision 3, 2026-07-15):
- Participation is per-user consent: only users with census_opt_in=True
  contribute to /census/export and /census/sync. Consent is toggled via
  PATCH /me.
- Operator-only: the export holds every participant's records, so it is not
  a user route. /census/export and /census/sync answer only a request that
  carries the operator credential (X-Operator-Token, compared in constant
  time with CENSUS_OPERATOR_TOKEN). With no credential configured they
  answer 404, as if they did not exist. A signed-in user is not an
  operator, and the app offers no way to call either.
- No stable pseudonymous identifiers: every identifier in an export is minted
  for that export. Growing areas get fresh UUIDs, and plants get a hash of
  their UUID under a salt drawn for the export and then discarded. Both are
  consistent within one payload (splits still read) and no identifier is
  shared by two exports.
- No position: records go out in a fresh random order (secrets.SystemRandom),
  so the nth record of one export is not the nth of the next.
- No precise times: care goes out as how many of each kind were logged in
  each calendar month, and acquisition and stewardship as months. A list of
  care dates is a fingerprint on its own -- a dozen watering days match one
  plant in a thousand -- so no day is exported.
- What is still possible, said plainly: a plant's monthly counts, species and
  city can resemble the same plant's in another export. The promise is that
  no identifier links two exports, not that nothing in them could.
- No precise location: lat/lng never leave the server; city/region/country
  only, and only for opted-in users.
- No human identity: no nicknames, no personal notes, no emails, ever.

/census/summary is the caller's own view of their garden — it requires auth
and covers only their data.
"""
import hashlib
import hmac
import os
import secrets
from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.deps import get_current_user
from app.models.models import (
    CareLog, GrowingArea, Plant, Species, StewardshipRecord, User,
)
from app.models.schemas import with_pre_rename_census_keys

router = APIRouter(prefix="/census", tags=["census"])


@router.get("/summary")
def census_summary(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Aggregate counts for the CALLER's garden — their population snapshot."""
    plants = session.exec(
        select(Plant).where(Plant.user_id == user.id)).all()
    growing_areas = session.exec(
        select(GrowingArea).where(GrowingArea.user_id == user.id)).all()
    species_list = session.exec(select(Species)).all()

    species_name_map = {s.id: s.common_name for s in species_list}
    env_map = {e.id: e for e in growing_areas}

    env_type_counts: dict[str, int] = {}
    for e in growing_areas:
        env_type_counts[e.type.value] = env_type_counts.get(e.type.value, 0) + 1

    # Count PLANTS, not rows. One row can stand for a whole planting — "twelve
    # tomatoes along the south fence" — so summing quantity is what keeps
    # "total_plants" true to its name. Rows created before quantity existed
    # carry the default of 1 and count exactly as they always did.
    plants_by_env_type: dict[str, int] = {}
    species_counts: dict[int, int] = {}
    for p in plants:
        env = env_map.get(p.growing_area_id) if p.growing_area_id else None
        env_label = env.type.value if env else "unassigned"
        qty = p.quantity or 1
        plants_by_env_type[env_label] = plants_by_env_type.get(env_label, 0) + qty
        species_counts[p.species_id] = species_counts.get(p.species_id, 0) + qty

    # The 1.1.2 app reads the area counts by their pre-rename keys; see the
    # pre-rename section of app/models/schemas.py.
    return with_pre_rename_census_keys({
        "total_plants": sum((p.quantity or 1) for p in plants),
        # Rows, which is also how many care schedules the caretaker actually
        # tends — twelve tomatoes watered together are one job, not twelve.
        "total_plantings": len(plants),
        "total_growing_areas": len(growing_areas),
        "growing_areas_by_type": env_type_counts,
        "plants_by_growing_area_type": plants_by_env_type,
        "species_distribution": [
            {
                "species_id": sid,
                "common_name": species_name_map.get(sid, "unknown"),
                "count": cnt,
            }
            for sid, cnt in sorted(species_counts.items(), key=lambda x: -x[1])
        ],
    })


def _opted_in_user_ids(session: Session) -> set[str]:
    rows = session.exec(
        select(User.id)
        .where(User.census_opt_in == True)  # noqa: E712
        .where(User.deleted_at == None)  # noqa: E711
    ).all()
    return set(rows)


#: The secret an operator presents to read or push the export. Unset (the
#: default) switches both routes off.
OPERATOR_TOKEN_ENV = "CENSUS_OPERATOR_TOKEN"


def require_operator(
    x_operator_token: Optional[str] = Header(default=None),
) -> None:
    """Let the request through only with the operator credential.

    No credential configured: 404, the same answer as a route that does not
    exist, so an unconfigured server does not advertise one. Configured but
    absent or wrong: 401. Compared with hmac.compare_digest, so the time a
    wrong guess takes says nothing about how close it was."""
    expected = os.getenv(OPERATOR_TOKEN_ENV, "")
    if not expected:
        raise HTTPException(status_code=404, detail="Not Found")
    if not x_operator_token or not hmac.compare_digest(
            x_operator_token.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Operator credential required")


def _new_export_salt() -> bytes:
    """A fresh secret per export, never stored. A seam for tests."""
    return secrets.token_bytes(32)


def _shuffle(records: list) -> None:
    """Put the records in a fresh random order, in place. A seam for tests.

    SystemRandom, not random: the order must not be reproducible by anyone
    who can guess a seed, or position would carry the database's row order
    across exports."""
    secrets.SystemRandom().shuffle(records)


def _month(moment) -> str:
    return moment.strftime("%Y-%m")


def plant_ref(salt: bytes, plant_uuid: str) -> str:
    """A plant's identifier within one export: its UUID hashed under that
    export's salt. The same plant (and a split's parent) reads the same all
    through one payload; with the salt gone, no two exports share a ref."""
    return hmac.new(salt, plant_uuid.encode(), hashlib.sha256).hexdigest()


def build_export(session: Session) -> dict:
    """Anonymized export of OPTED-IN users' plant records.

    Every identifier is minted for this export: growing areas get fresh
    UUIDs and plants a salted hash (plant_ref), consistent within this
    payload so splits stay meaningful, but never the same twice. Records
    are shuffled, care is counted per month, and every time is a month, so
    neither position nor a run of care dates identifies a plant across
    exports. Locations are city/region/country only -- lat/lng never leave
    the server."""
    opted = _opted_in_user_ids(session)
    plants = session.exec(select(Plant)).all()
    plants = [p for p in plants if p.user_id in opted]

    salt = _new_export_salt()

    # Per-export rotation map: real env id -> ephemeral UUID
    rotated: dict[int, str] = {}

    def rotated_uuid(env_id: int) -> str:
        if env_id not in rotated:
            rotated[env_id] = str(uuid4())
        return rotated[env_id]

    records = []
    for plant in plants:
        env = session.get(GrowingArea, plant.growing_area_id) if plant.growing_area_id else None

        logs = session.exec(
            select(CareLog).where(CareLog.plant_id == plant.id)
        ).all()
        # How many of each kind in each calendar month: enough to study
        # care patterns, and no day that would single the plant out.
        care_by_type: dict[str, dict[str, int]] = {}
        for log in logs:
            months = care_by_type.setdefault(log.action.value, {})
            month = _month(log.logged_at)
            months[month] = months.get(month, 0) + 1
        care_history = {action: dict(sorted(months.items()))
                        for action, months in sorted(care_by_type.items())}

        stewardship = session.exec(
            select(StewardshipRecord)
            .where(StewardshipRecord.plant_id == plant.id)
            .order_by(StewardshipRecord.started_at.asc())
        ).all()

        # When each stewardship began and ended, as months, and nothing
        # else: the day a plant was added is near-unique, and the area it
        # was in is the record's own growing_area.
        stewardship_chain = [
            {"started_month": _month(rec.started_at),
             "ended_month": _month(rec.ended_at) if rec.ended_at else None}
            for rec in stewardship
        ]

        records.append({
            # This export's name for the plant, never its real UUID.
            "plant_ref": plant_ref(salt, plant.plant_uuid),
            # How many physical plants this record stands for. Without it a
            # bed of twelve tomatoes would export as indistinguishable from a
            # single plant on a windowsill.
            "quantity": plant.quantity or 1,
            # Set when this record was split off another planting: the
            # parent's plant_ref in this same export. The pair was once
            # counted as one plant, so an aggregator needs this to avoid
            # reading a split as newly appeared plants.
            "split_from_ref": plant_ref(salt, plant.split_from_uuid)
            if plant.split_from_uuid else None,
            "species_id": plant.species_id,
            "maturity_stage": plant.maturity_stage.value,
            "acquired_month": _month(plant.acquired_on)
            if plant.acquired_on else None,
            # Location dimension: geographic region only — never lat/lng
            "growing_area": {
                "ref": rotated_uuid(env.id),
                "type": env.type.value,
                "city": env.city,
                "region": env.region,
                "country": env.country,
            } if env else None,
            "stewardship_chain": stewardship_chain,
            "stewardship_count": len(stewardship),
            "care_history": care_history,
            "initial_condition": {
                "soil_moisture": plant.soil_moisture_at_acquisition.value
                    if plant.soil_moisture_at_acquisition else None,
                "leaf_condition": plant.leaf_condition_at_acquisition.value
                    if plant.leaf_condition_at_acquisition else None,
                "pest_observed": plant.pest_observed_at_acquisition,
            },
        })

    # Position would otherwise be the database's row order, the same in
    # every export: record n of one would be record n of the next.
    _shuffle(records)

    return {
        # 4.1 takes out what still matched a plant across exports when no
        # identifier did: records are shuffled; `care_history` is counts per
        # care type per calendar month ({"water": {"2026-05": 4}}) instead
        # of a list of dates; the stewardship chain is `started_month` and
        # `ended_month` only, without its area ref and type. Minor, because
        # the keys an aggregator reads for everything else are unchanged.
        #
        # 4.0 stops exporting anything stable enough to link two exports:
        # `plant_uuid` and `split_from_uuid` are `plant_ref` and
        # `split_from_ref`, salted per export; care and stewardship times
        # are dates (`started_at`/`ended_at` are `started_on`/`ended_on`);
        # `acquired_on` is `acquired_month`. Major, because an aggregator
        # reading 3.0 keys finds nothing under them.
        #
        # 3.0 renamed the location dimension: `environment` is
        # `growing_area`, and inside the stewardship chain
        # `environment_ref`/`environment_type` are
        # `growing_area_ref`/`growing_area_type`.
        #
        # 2.1 added per-record `quantity` and the split link. Bumped rather
        # than added silently because `plant_count` changed meaning with it:
        # it counts plants, as its name always claimed, instead of rows.
        "export_version": "4.1",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "installation_uuid": os.getenv("INSTALLATION_UUID", ""),
        "plant_count": sum(r["quantity"] for r in records),
        "planting_count": len(records),
        "plants": records,
    }


@router.get("/export", dependencies=[Depends(require_operator)],
            include_in_schema=False)
def census_export(session: Session = Depends(get_session)):
    """The export, for the operator (see require_operator)."""
    return build_export(session)


@router.post("/sync", dependencies=[Depends(require_operator)],
             include_in_schema=False)
def census_sync(session: Session = Depends(get_session)):
    """Push the anonymized, consent-filtered export to CENSUS_API_URL.

    An operator job, not a user action. If no URL is configured, returns a
    'skipped' status and sends nothing."""
    census_url = os.getenv("CENSUS_API_URL", "").rstrip("/")
    if not census_url:
        return {
            "status": "skipped",
            "reason": "CENSUS_API_URL is not set, so nothing was sent",
        }
    try:
        import httpx
        payload = build_export(session)
        resp = httpx.post(f"{census_url}/ingest", json=payload, timeout=30.0)
        resp.raise_for_status()
        return {
            "status": "ok",
            "records_sent": len(payload["plants"]),
            "census_url": census_url,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Census sync failed: {exc}",
        ) from exc
