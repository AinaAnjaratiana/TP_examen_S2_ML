"""Outil de consultation : consulter_equipement."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "equipements.json"


def _charger():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as fichier:
        return json.load(fichier)


def consulter_equipement(equipement_id):
    if equipement_id is None:
        return None
    for equipement in _charger():
        if equipement["id"] == equipement_id:
            return equipement
    return None


def lister_equipements_utilisateur(utilisateur_id):
    return [e for e in _charger() if e["utilisateur_id"] == utilisateur_id]
