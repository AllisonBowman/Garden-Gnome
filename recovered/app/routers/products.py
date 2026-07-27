"""Amazon product recommendations mapped to the species catalog.

Routes live under /products rather than being grafted onto /species and
/plants so the whole affiliate surface is one file that can be removed in one
line of main.py — a monetization feature should never be load-bearing for
plant care.

Two levels of personalization:

* `/products/species/{id}` — everything derivable from the species record.
  Unauthenticated, matching the rest of /species: this is catalog data, and
  the Add Plant / species browse flows need it before a plant exists.
* `/products/plants/{id}` — the same, re-ranked against *this* plant's care
  log, so gear for care that is actually overdue floats to the top.
  Authenticated and user-scoped, 404 on someone else's plant like every other
  plant route.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.db.database import get_session
from app.deps import get_current_user
from app.models.models import (
    CareLog, CareSchedule, CareType, Plant, Species, SpeciesTrait, User,
)
from app.services import affiliate, products

router = APIRouter(prefix="/products", tags=["products"])

MAX_PER_CATEGORY = 6


def _load_species(species_id: int, session: Session) -> Species:
    species = session.exec(
        select(Species)
        .where(Species.id == species_id)
        .options(selectinload(Species.care_schedules), selectinload(Species.traits))
    ).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    return species


def _due_care_types(plant: Plant, session: Session) -> list[str]:
    """Care types past the species' scheduled window for this plant.

    Same rule the rule-based advisor uses — days since the last log of that
    type exceeding `interval_days_max`. A care type that has never been logged
    counts as due; that is the state where a user is most likely to be missing
    the equipment for it."""
    schedules = session.exec(
        select(CareSchedule).where(CareSchedule.species_id == plant.species_id)
    ).all()
    if not schedules:
        return []

    logs = session.exec(
        select(CareLog)
        .where(CareLog.plant_id == plant.id)
        .order_by(CareLog.logged_at.desc())
    ).all()
    last_by_type: dict[CareType, datetime] = {}
    for log in logs:
        last_by_type.setdefault(log.action, log.logged_at)

    now = datetime.utcnow()
    due = []
    for cs in schedules:
        last = last_by_type.get(cs.care_type)
        if last is None or (now - last).days > cs.interval_days_max:
            due.append(cs.care_type.value)
    return due


@router.get("/categories")
def list_categories():
    """The product category taxonomy, in display order."""
    return {"categories": products.category_list(), **affiliate.link_meta()}


@router.get("/status")
def affiliate_status():
    """Whether this deployment has a working Associates tag.

    Exposed so the client can hide monetized UI on an unconfigured build and
    so a missing tag is visible in production rather than quietly costing
    every click."""
    return {
        **affiliate.link_meta(),
        "catalog_version": products.load_catalog().get("version"),
        "product_count": len(products.load_catalog()["products"]),
        "link_strategy": "scoped-search",
    }


@router.get("/species/{species_id}")
def products_for_species(
    species_id: int,
    per_category: int = Query(products.DEFAULT_PER_CATEGORY, ge=1, le=MAX_PER_CATEGORY),
    category: Optional[list[str]] = Query(None),
    session: Session = Depends(get_session),
):
    """Product recommendations derived from this species' care record."""
    species = _load_species(species_id, session)
    return products.recommend_for_species(
        species,
        schedules=species.care_schedules,
        traits=species.traits,
        per_category=per_category,
        categories=category,
    )


@router.get("/plants/{plant_id}")
def products_for_plant(
    plant_id: int,
    per_category: int = Query(products.DEFAULT_PER_CATEGORY, ge=1, le=MAX_PER_CATEGORY),
    category: Optional[list[str]] = Query(None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Recommendations for one of the caller's plants, ranked with overdue
    care first. 404 for a plant the caller doesn't own — never 403, so plant
    ids can't be probed (same rule as every other plant route)."""
    plant = session.get(Plant, plant_id)
    if plant is None or plant.user_id != user.id:
        raise HTTPException(status_code=404, detail="Plant not found")

    species = _load_species(plant.species_id, session)
    due = _due_care_types(plant, session)
    payload = products.recommend_for_species(
        species,
        schedules=species.care_schedules,
        traits=species.traits,
        per_category=per_category,
        categories=category,
        due_care_types=due,
    )
    payload["plant"] = {
        "id": plant.id,
        "nickname": plant.nickname,
        "due_care_types": due,
    }
    return payload
