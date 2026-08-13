"""Observabilité : mesure de latence des appels d'outils et journal des traces.

Chaque requête traitée par l'agent produit une trace complète (entrée, appels
d'outils avec paramètres/résultat/statut/latence, sortie, latence totale) qui
est ajoutée à data/observabilite.json. Ce fichier sert de journal / tableau de
bord d'observabilité, consultable via GET /api/observabilite/traces ou
frontend/dashboard.html.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parents[2] / "data" / "observabilite.json"
LIMITE_TRACES = 500


def _charger():
    if not LOG_FILE.exists():
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as fichier:
        return json.load(fichier)


def _sauvegarder(traces):
    with open(LOG_FILE, "w", encoding="utf-8") as fichier:
        json.dump(traces, fichier, ensure_ascii=False, indent=2)


def enregistrer_trace(trace):
    traces = _charger()
    traces.append(trace)
    traces = traces[-LIMITE_TRACES:]
    _sauvegarder(traces)


def obtenir_traces(limite=50):
    traces = _charger()
    return list(reversed(traces[-limite:]))


def reinitialiser_traces():
    """Vide le journal de traces (utile pour les tests)."""
    _sauvegarder([])


def appeler_outil(nom_outil, parametres, fonction):
    """Exécute un outil en mesurant sa latence et en capturant les erreurs.

    Retourne (resultat, trace) où trace contient : outil, parametres, resultat,
    statut ('succes' | 'erreur'), erreur, latence_ms, horodatage.
    """
    debut = time.perf_counter()
    statut = "succes"
    erreur = None
    resultat = None

    try:
        resultat = fonction(**parametres)
    except Exception as exc:  # pragma: no cover - garde-fou générique
        statut = "erreur"
        erreur = str(exc)

    latence_ms = round((time.perf_counter() - debut) * 1000, 2)

    trace = {
        "outil": nom_outil,
        "parametres": parametres,
        "resultat": resultat,
        "statut": statut,
        "erreur": erreur,
        "latence_ms": latence_ms,
        "horodatage": datetime.now(timezone.utc).isoformat(),
    }

    return resultat, trace
