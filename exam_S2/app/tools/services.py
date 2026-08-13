"""Outil de consultation : verifier_etat_service."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "services.json"


def _charger():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as fichier:
        return json.load(fichier)


def verifier_etat_service(nom_service):
    """Recherche approximative : fonctionne même si le nom ne correspond pas exactement."""
    services = _charger()
    nom_normalise = (nom_service or "").lower()

    for service in services:
        if service["nom"].lower() == nom_normalise:
            return service

    for service in services:
        if nom_normalise in service["nom"].lower() or service["nom"].lower() in nom_normalise:
            return service

    return {"nom": nom_service, "etat": "inconnu"}
