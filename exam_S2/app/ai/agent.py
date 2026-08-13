"""Agent : orchestration complète du traitement d'un ticket.

Chaîne : sécurité -> outils de consultation (utilisateur, équipement, état du
service, incidents actifs) -> classification -> recherche documentaire (RAG)
-> détection des informations manquantes -> décision (résolution / demande
d'information / escalade) -> création et mise à jour du ticket -> sortie
structurée + trace d'observabilité.
"""

import time
from datetime import datetime, timezone

from app.ai.rag import rechercher_dans_base
from app.ai.security import analyser_securite
from app.core.observabilite import appeler_outil, enregistrer_trace
from app.tools.equipements import consulter_equipement
from app.tools.incidents import rechercher_incidents_actifs
from app.tools.services import verifier_etat_service
from app.tools.tickets import creer_ticket, escalader_vers_technicien, mettre_a_jour_ticket
from app.tools.utilisateurs import rechercher_utilisateur

CATEGORIES_MOTS_CLES = {
    "Comptes et authentification": [
        "mot de passe", "mdp", "compte verrouillé", "compte bloqué",
        "connexion impossible", "identifiant", "authentification", "code de validation",
    ],
    "Réseau et connectivité": [
        "internet", "wifi", "wi-fi", "réseau", "connexion lente", "vpn", "câble réseau", "déconnecté",
    ],
    "Matériel informatique": [
        "ordinateur", " pc ", "pc ", "écran", "clavier", "souris", "portable",
        "batterie", "ne démarre", "démarre plus", "allume pas",
    ],
    "Logiciels et applications": [
        "application", "logiciel", "programme", "plante", "bug", "mise à jour",
        "ne s'ouvre", "erreur logicielle",
    ],
    "Imprimantes et périphériques": [
        "imprimante", "impression", "imprimer", "scanner", "photocopieuse", "cartouche", "bourrage",
    ],
    "Droits d'accès": [
        "accès", "droits", "partage", "dossier partagé", "autorisation", "permission", "licence",
    ],
    "Cybersécurité": [
        "phishing", "hameçonnage", "virus", "ransomware", "courriel suspect",
        "email suspect", "piraté", "compromis", "malware", "logiciel malveillant",
    ],
}

EQUIPES = {
    "Comptes et authentification": "Support informatique",
    "Réseau et connectivité": "Équipe réseau",
    "Matériel informatique": "Support informatique",
    "Logiciels et applications": "Support informatique",
    "Imprimantes et périphériques": "Support informatique",
    "Droits d'accès": "Support informatique",
    "Cybersécurité": "Équipe sécurité",
    "Autre ou indéterminé": "Support informatique",
}

MOTS_URGENCE_HAUTE = ["urgent", "bloqué", "impossible de travailler", "ne peux plus travailler", "production"]
MOTS_URGENCE_CRITIQUE = [
    "serveur down", "tout le service", "toute l'équipe", "aucun accès",
    "panne générale", "personne ne peut", "plusieurs utilisateurs",
]

ETAPES_PAR_DEFAUT = [
    "Un technicien doit analyser le problème plus en détail.",
]


def _classifier(description):
    texte = description.lower()
    scores = {}

    for categorie, mots in CATEGORIES_MOTS_CLES.items():
        score = sum(1 for mot in mots if mot in texte)
        if score:
            scores[categorie] = score

    if not scores:
        return "Autre ou indéterminé", 0.4

    categorie = max(scores, key=scores.get)
    confiance = min(0.5 + 0.15 * scores[categorie], 0.95)
    return categorie, confiance


def _determiner_priorite(description, categorie):
    texte = description.lower()

    if categorie == "Cybersécurité" or any(mot in texte for mot in MOTS_URGENCE_CRITIQUE):
        return "Critique"
    if any(mot in texte for mot in MOTS_URGENCE_HAUTE):
        return "Haute"
    return "Moyenne"


def _extraire_informations_manquantes(description, equipement_id):
    manquantes = []
    texte = description.lower()

    if len(description.strip()) < 15:
        manquantes.append("Description du problème trop succincte")

    if equipement_id is None and any(
        mot in texte for mot in ["ordinateur", "pc", "imprimante", "écran", "portable"]
    ):
        manquantes.append("Identifiant de l'équipement concerné")

    if not any(mot in texte for mot in ["depuis", "aujourd'hui", "hier", "ce matin", "cette semaine", "matin", "soir"]):
        manquantes.append("Moment d'apparition du problème")

    return manquantes


def _generer_etapes(sources):
    if not sources:
        return list(ETAPES_PAR_DEFAUT)

    etapes = []
    for source in sources:
        lignes = [l.strip() for l in source["extrait"].split("\n") if l.strip()]
        # la première ligne est le titre du passage ; le reste contient les instructions
        for ligne in lignes[1:]:
            for phrase in ligne.split(". "):
                phrase = phrase.strip().rstrip(".")
                if phrase and len(phrase) > 10:
                    etapes.append(phrase + ".")
    return etapes[:5] if etapes else list(ETAPES_PAR_DEFAUT)


def traiter_ticket(utilisateur_id, description, equipement_id=None):
    debut_total = time.perf_counter()
    traces_outils = []

    # 1. Analyse de sécurité (injection de prompt, action sensible, données personnelles)
    securite = analyser_securite(description)

    # 2. Consultation de l'utilisateur
    utilisateur, trace = appeler_outil(
        "rechercher_utilisateur", {"utilisateur_id": utilisateur_id}, rechercher_utilisateur
    )
    traces_outils.append(trace)

    # 3. Consultation de l'équipement si fourni
    equipement = None
    if equipement_id is not None:
        equipement, trace = appeler_outil(
            "consulter_equipement", {"equipement_id": equipement_id}, consulter_equipement
        )
        traces_outils.append(trace)

    # 4. Classification et priorisation
    categorie, confiance_classification = _classifier(description)
    priorite = _determiner_priorite(description, categorie)
    equipe = EQUIPES.get(categorie, "Support informatique")

    # 5. État du service concerné
    etat_service, trace = appeler_outil(
        "verifier_etat_service", {"nom_service": equipe}, verifier_etat_service
    )
    traces_outils.append(trace)

    # 6. Incidents actifs liés à cette catégorie
    incidents_actifs, trace = appeler_outil(
        "rechercher_incidents_actifs", {"categorie": categorie}, rechercher_incidents_actifs
    )
    traces_outils.append(trace)

    # 7. Recherche documentaire (RAG)
    debut_rag = time.perf_counter()
    sources = rechercher_dans_base(description, top_k=3)
    latence_rag_ms = round((time.perf_counter() - debut_rag) * 1000, 2)

    # 8. Informations manquantes -> questions ciblées
    informations_manquantes = _extraire_informations_manquantes(description, equipement_id)
    questions = [f"Pouvez-vous préciser : {m.lower()} ?" for m in informations_manquantes]

    # 9. Diagnostic fondé sur les sources retrouvées
    if sources:
        diagnostic = sources[0]["titre"]
        confiance_rag = sources[0]["score"]
    else:
        diagnostic = "Aucune procédure correspondante n'a été retrouvée dans la base de connaissances."
        confiance_rag = 0.0

    confiance = round((confiance_classification + min(confiance_rag * 2, 1)) / 2, 2)
    etapes_resolution = _generer_etapes(sources)

    # 10. Décision finale
    if securite["injection_detectee"]:
        action = "escalade"
        raison_escalade = (
            "Contenu suspect détecté dans la description (tentative d'instruction "
            "non autorisée) — aucune action automatique n'a été exécutée."
        )
    elif incidents_actifs and priorite in ("Haute", "Critique"):
        action = "escalade"
        raison_escalade = "Incident actif correspondant déjà déclaré et priorité élevée."
    elif informations_manquantes:
        action = "demande_information"
        raison_escalade = None
    elif not sources or confiance < 0.6:
        action = "escalade"
        raison_escalade = "Confiance insuffisante ou absence de source documentaire pertinente."
    else:
        action = "resolution"
        raison_escalade = None

    validation_humaine_requise = (
        securite["validation_requise"]
        or categorie == "Cybersécurité"
        or priorite in ("Haute", "Critique")
        or confiance < 0.6
    )

    # 11. Création puis mise à jour du ticket
    ticket = creer_ticket(
        utilisateur_id=utilisateur_id, description=description, equipement_id=equipement_id
    )

    statut = {
        "escalade": "Escaladé",
        "demande_information": "En attente d'information",
        "resolution": "Résolu",
    }[action]

    mettre_a_jour_ticket(ticket["id"], categorie=categorie, priorite=priorite, equipe=equipe, statut=statut)

    if action == "escalade":
        escalader_vers_technicien(ticket["id"], raison=raison_escalade)

    resultat = {
        "ticket_id": ticket["id"],
        "resume": description.strip()[:200],
        "categorie": categorie,
        "priorite": priorite,
        "equipe": equipe,
        "confiance": confiance,
        "informations_manquantes": informations_manquantes,
        "diagnostic": diagnostic,
        "etapes_resolution": etapes_resolution,
        "questions": questions,
        "sources": [
            {"id": s["id"], "nom": s["document"], "score": s["score"]} for s in sources
        ],
        "outils_utilises": [t["outil"] for t in traces_outils],
        "action": action,
        "validation_humaine_requise": validation_humaine_requise,
        "securite": securite,
        "contexte": {
            "utilisateur": utilisateur,
            "equipement": equipement,
            "etat_service": etat_service,
            "incidents_actifs": incidents_actifs,
        },
        "logs": [
            f"Ticket #{ticket['id']} créé"
        ] + [
            f"{t['outil']} -> {t['statut']} ({t['latence_ms']} ms)" for t in traces_outils
        ] + [
            f"rag -> {len(sources)} source(s) trouvée(s) ({latence_rag_ms} ms)",
            f"Catégorie retenue : {categorie} (confiance {confiance})",
            f"Décision : {action}" + (f" — {raison_escalade}" if raison_escalade else ""),
        ],
    }

    latence_totale_ms = round((time.perf_counter() - debut_total) * 1000, 2)

    enregistrer_trace(
        {
            "horodatage": datetime.now(timezone.utc).isoformat(),
            "ticket_id": ticket["id"],
            "entree": {
                "utilisateur_id": utilisateur_id,
                "description": description,
                "equipement_id": equipement_id,
            },
            "sortie": resultat,
            "appels_outils": traces_outils,
            "latence_rag_ms": latence_rag_ms,
            "latence_totale_ms": latence_totale_ms,
        }
    )

    return resultat
