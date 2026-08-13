"""Outil : gestion des tickets (creer_ticket, mettre_a_jour_ticket, affecter_ticket,
escalader_vers_technicien). Persistance simple dans un fichier JSON."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "tickets.json"


def charger_tickets():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as fichier:
        return json.load(fichier)


def sauvegarder_tickets(tickets):
    with open(DATA_FILE, "w", encoding="utf-8") as fichier:
        json.dump(tickets, fichier, ensure_ascii=False, indent=4)


def creer_ticket(utilisateur_id, description, equipement_id=None):
    tickets = charger_tickets()

    nouveau_id = max((t["id"] for t in tickets), default=0) + 1

    ticket = {
        "id": nouveau_id,
        "utilisateur_id": utilisateur_id,
        "description": description,
        "equipement_id": equipement_id,
        "categorie": None,
        "priorite": "Moyenne",
        "equipe": None,
        "statut": "Ouvert",
    }

    tickets.append(ticket)
    sauvegarder_tickets(tickets)
    return ticket


def obtenir_tickets():
    return charger_tickets()


def obtenir_ticket(ticket_id):
    for ticket in charger_tickets():
        if ticket["id"] == ticket_id:
            return ticket
    return None


def mettre_a_jour_ticket(ticket_id, **champs):
    """Met à jour un ou plusieurs champs d'un ticket existant (categorie, priorite, statut, ...)."""
    tickets = charger_tickets()
    ticket_maj = None

    for ticket in tickets:
        if ticket["id"] == ticket_id:
            ticket.update(champs)
            ticket_maj = ticket
            break

    if ticket_maj is not None:
        sauvegarder_tickets(tickets)

    return ticket_maj


def affecter_ticket(ticket_id, equipe):
    return mettre_a_jour_ticket(ticket_id, equipe=equipe)


def escalader_vers_technicien(ticket_id, raison="Intervention technique nécessaire"):
    tickets = charger_tickets()

    for ticket in tickets:
        if ticket["id"] == ticket_id:
            ticket["statut"] = "Escaladé"
            ticket["raison_escalade"] = raison
            ticket["technicien"] = None
            sauvegarder_tickets(tickets)
            return ticket

    return None
