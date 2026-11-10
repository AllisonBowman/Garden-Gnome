"""Reading the census export the only way it can be read: as the operator.

The export is not a user route (app/routers/census.py, require_operator), so
tests that inspect it switch the operator credential on and present it. A
test that needs to find its own plant in an export pins the export's salt and
computes the plant's ref the way the router does.
"""
from app.routers import census

OPERATOR_TOKEN = "test-operator-token-0123456789abcdef"  # >= 32 characters
OPERATOR_HEADERS = {"X-Operator-Token": OPERATOR_TOKEN}
PINNED_SALT = b"pinned-salt-for-tests-only-32byt"


def as_operator(monkeypatch) -> dict:
    """Switch the operator routes on for this test; return the headers."""
    monkeypatch.setenv(census.OPERATOR_TOKEN_ENV, OPERATOR_TOKEN)
    return OPERATOR_HEADERS


def pin_salt(monkeypatch) -> None:
    """Every export in this test hashes under PINNED_SALT."""
    monkeypatch.setattr(census, "_new_export_salt", lambda: PINNED_SALT)


def ref(plant_uuid: str) -> str:
    """What a pinned-salt export calls the plant with this UUID."""
    return census.plant_ref(PINNED_SALT, plant_uuid)


def export(client, monkeypatch) -> dict:
    """One export, read as the operator."""
    response = client.get("/census/export", headers=as_operator(monkeypatch))
    assert response.status_code == 200, response.text
    return response.json()
