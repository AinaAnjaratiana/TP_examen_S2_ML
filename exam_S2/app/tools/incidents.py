"""Outil de consultation : rechercher_incidents_actifs."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "incidents.json"


def _charger():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as fichier:
        return json.load(fichier)


def rechercher_incidents_actifs(categorie=None):
    incidents = _charger()
    if categorie is None:
        return incidents
    return [i for i in incidents if i.get("categorie") == categorie]
