"""Garde-fous de sécurité : détection d'injection de prompt, d'actions sensibles
et de données personnelles dans la description d'un ticket.

Ce module ne bloque jamais silencieusement : il renvoie un diagnostic exploité
par l'agent (app/ai/agent.py) pour décider s'il faut refuser une action, forcer
une validation humaine, ou simplement journaliser un avertissement.
"""

import re

MOTS_CLES_INJECTION = [
    "ignore les instructions",
    "ignore toutes les instructions",
    "ignore previous instructions",
    "oublie tes instructions",
    "oublie tes consignes",
    "tu es maintenant",
    "nouveau rôle",
    "system prompt",
    "révèle ton prompt",
    "affiche ton prompt",
    "donne-moi le mot de passe",
    "donne moi le mot de passe",
    "envoie-moi tous les mots de passe",
    "désactive la sécurité",
    "désactive la validation",
    "sans validation humaine",
    "agis comme root",
    "sudo",
    "accès administrateur complet",
    "supprime tous les tickets",
    "contourne la procédure",
    "bypass",
    "ne demande pas d'autorisation",
]

ACTIONS_SENSIBLES = [
    "réinitialiser le mot de passe",
    "réinitialise le mot de passe",
    "reset password",
    "modifier les droits",
    "donner les droits admin",
    "donner l'accès admin",
    "supprimer le compte",
    "incident de sécurité",
    "compte compromis",
    "poste compromis",
    "courriel suspect",
    "email suspect",
    "phishing",
    "hameçonnage",
    "ransomware",
    "virus",
    "logiciel malveillant",
]

REGEX_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
REGEX_TELEPHONE = re.compile(r"\b0\d(?:[ .-]?\d{2}){4}\b")


def analyser_securite(texte: str) -> dict:
    texte_normalise = (texte or "").lower()

    injection_detectee = any(mot in texte_normalise for mot in MOTS_CLES_INJECTION)
    action_sensible = any(mot in texte_normalise for mot in ACTIONS_SENSIBLES)
    donnees_personnelles = bool(REGEX_EMAIL.search(texte or "")) or bool(
        REGEX_TELEPHONE.search(texte or "")
    )

    return {
        "injection_detectee": injection_detectee,
        "action_sensible": action_sensible,
        "donnees_personnelles_detectees": donnees_personnelles,
        "validation_requise": injection_detectee or action_sensible,
    }
