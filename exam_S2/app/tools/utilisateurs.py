"""Outil de consultation : rechercher_utilisateur."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "users.json"


def _charger():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as fichier:
        return json.load(fichier)


def rechercher_utilisateur(utilisateur_id):
    for utilisateur in _charger():
        if utilisateur["id"] == utilisateur_id:
            return utilisateur
    return None


def lister_utilisateurs():
    return _charger()
