# mAIntenance & Assistance

ANDRIANJOHANY Liantsoa Nomban'Ny Avo,IGGLIA5 N 07
ANDRIANANDRASANA Finiaina,IGGLIA5 N 43
RAKOTOMALALA Aina Anjaratiana, IGGLIA5 N 30
RAHARINAIVO Faramampionona, IGGLIA5 N 52

> Comprendre. Diagnostiquer. Assister. Résoudre.

## 1. Démarrage rapide

```bash
pip install -r requirements.txt --break-system-packages
uvicorn app.main:app --reload
```

Puis ouvrir : http://127.0.0.1:8000/ (interface assistant) et http://127.0.0.1:8000/dashboard.html (observabilité).

Documentation API interactive (générée par FastAPI) : http://127.0.0.1:8000/docs

Lancer le jeu de tests des 4 scénarios obligatoires :

```bash
python3 tests/test_scenarios.py
```

Les résultats sont enregistrés dans `data/evaluation_results.json`.

## 2. Architecture

```
app/
├── main.py                 point d'entrée FastAPI, montage du frontend statique
├── api/
│   ├── assistant.py         POST /api/assistant/analyser
│   ├── tickets.py           GET  /api/tickets, /api/tickets/{id}
│   ├── utilisateurs.py       GET  /api/utilisateurs
│   └── observabilite.py     GET  /api/observabilite/traces
├── ai/
│   ├── agent.py             orchestrateur : classification, appels d'outils, RAG, décision
│   ├── rag.py                recherche documentaire (TF-IDF pur Python)
│   └── security.py          détection d'injection / actions sensibles / données personnelles
├── models/
│   └── schemas.py           schémas Pydantic (TicketCreate, Ticket, ResultatAnalyse)
├── tools/                   outils appelables par l'agent
│   ├── tickets.py            creer_ticket, mettre_a_jour_ticket, affecter_ticket, escalader_vers_technicien
│   ├── utilisateurs.py       rechercher_utilisateur
│   ├── equipements.py        consulter_equipement
│   ├── services.py           verifier_etat_service
│   └── incidents.py          rechercher_incidents_actifs
└── core/
    └── observabilite.py     mesure de latence, journal des traces (data/observabilite.json)

data/
├── tickets.json, users.json, equipements.json, services.json, incidents.json
├── knowledge/               base de connaissances (RAG) : 8 fichiers texte
├── observabilite.json       journal des traces (généré à l'exécution)
└── evaluation_results.json  résultats du jeu de tests (généré par tests/test_scenarios.py)

frontend/
├── index.html, app.js, style.css     interface de soumission de ticket
└── dashboard.html, dashboard.js      tableau de bord d'observabilité

tests/
└── test_scenarios.py        les 4 scénarios obligatoires du sujet
```

### Chaîne de traitement (correspond au schéma du sujet)

```
Ticket (langage naturel)
   → analyse de sécurité (injection, action sensible, données personnelles)
   → appels d'outils de consultation (utilisateur, équipement, état du service, incidents actifs)
   → classification (catégorie, priorité, équipe)
   → recherche documentaire RAG (sources + score de confiance)
   → détection des informations manquantes → questions ciblées
   → décision : resolution | demande_information | escalade
   → création/mise à jour du ticket
   → sortie structurée (JSON conforme au schéma du sujet)
   → trace complète enregistrée pour l'observabilité
```

## 3. Approche de classification et de routage

Approche par **règles pondérées sur mots-clés** (pas de ML entraîné) : chaque description est comparée à des
listes de mots-clés par catégorie (`app/ai/agent.py::CATEGORIES_MOTS_CLES`), la catégorie au score le plus élevé
est retenue, la confiance croît avec le nombre de mots-clés trouvés. La priorité est déduite de mots signalant
l'urgence ou la criticité (`urgent`, `bloqué`, `serveur down`, incidents touchant plusieurs utilisateurs, catégorie
Cybersécurité → priorité automatiquement critique).

**Justification du choix** : dans le temps imparti (hackathon), une approche par règles est rapide à mettre en
œuvre, entièrement explicable (traçable mot-clé par mot-clé), ne nécessite aucune donnée d'entraînement et reste
facilement substituable par un classifieur ML ou un LLM sans changer l'interface (`_classifier` retourne toujours
`(categorie, confiance)`).

**Limites connues** : sensible aux synonymes et fautes d'orthographe non prévus dans les listes de mots-clés ;
ne gère pas la négation (« mon imprimante marche très bien » serait mal classée) ; les scores de confiance sont
heuristiques et non calibrés statistiquement.

## 4. Système RAG (`app/ai/rag.py`)

- **Ingestion** : chaque fichier de `data/knowledge/*.txt` est découpé en passages séparés par une ligne vide.
- **Indexation** : vecteurs TF-IDF calculés en pur Python (aucune dépendance externe : `math`, `re`, `collections`).
- **Recherche** : similarité cosinus entre la requête et chaque passage, tri par score décroissant, seuil de
  pertinence (0.05) en dessous duquel un passage n'est pas retenu.
- **Citation des sources** : chaque réponse renvoie `sources: [{id, nom, score}]` ; si aucune source ne dépasse
  le seuil, `sources` est vide et le diagnostic est explicitement marqué incertain (confiance basse →
  `validation_humaine_requise = true`).
- **Évolution prévue** : remplacer le TF-IDF par des embeddings (ex. `sentence-transformers`) et une base
  vectorielle (FAISS/Chroma) sans changer l'interface publique `rechercher_dans_base(requete, top_k)`.

## 5. Agent et outils

L'agent (`app/ai/agent.py::traiter_ticket`) sélectionne et appelle des outils réels (lecture/écriture sur fichiers
JSON simulant une base de données) :

| Outil | Type | Rôle |
|---|---|---|
| `rechercher_utilisateur` | consultation | vérifie l'existence et récupère le profil de l'utilisateur |
| `consulter_equipement` | consultation | récupère les informations de l'équipement si fourni |
| `verifier_etat_service` | consultation | vérifie si le service concerné est opérationnel/dégradé |
| `rechercher_incidents_actifs` | consultation | détecte un incident global déjà déclaré dans la même catégorie |
| `creer_ticket` | action | crée le ticket en base |
| `mettre_a_jour_ticket` | action | met à jour catégorie/priorité/statut |
| `affecter_ticket` | action | affecte le ticket à une équipe |
| `escalader_vers_technicien` | action | bascule le ticket en statut « Escaladé » avec une raison tracée |

Chaque appel passe par `app/core/observabilite.py::appeler_outil`, qui mesure la latence, capture les erreurs
éventuelles et journalise systématiquement `{outil, parametres, resultat, statut, latence_ms, horodatage}`.

Aucune action sensible (réinitialisation, modification de droits, incident de sécurité) n'est exécutée
automatiquement : ces cas sont toujours orientés vers `action = "escalade"` avec `validation_humaine_requise = true`.

## 6. Sorties structurées

Chaque appel à `/api/assistant/analyser` renvoie un objet JSON conforme au schéma du sujet (section 5.3), enrichi
des champs utiles à la démonstration :

```json
{
  "ticket_id": 4,
  "categorie": "Matériel informatique",
  "priorite": "Moyenne",
  "equipe": "Support informatique",
  "confiance": 0.94,
  "informations_manquantes": [],
  "diagnostic": "...",
  "etapes_resolution": ["...", "..."],
  "questions": [],
  "sources": [{"id": "ordinateurs-1", "nom": "ordinateurs.txt", "score": 0.62}],
  "outils_utilises": ["rechercher_utilisateur", "verifier_etat_service", "rechercher_incidents_actifs"],
  "action": "resolution",
  "validation_humaine_requise": false,
  "logs": ["..."]
}
```

## 7. Observabilité

Chaque requête traitée génère une trace complète (entrée, tous les appels d'outils avec leurs paramètres/résultats/
statuts/latences, sortie finale, latence RAG, latence totale) enregistrée dans `data/observabilite.json`
(les 500 dernières traces sont conservées). Le tableau de bord `frontend/dashboard.html` interroge
`GET /api/observabilite/traces` et affiche pour chaque ticket : décision, confiance, latences, table des appels
d'outils et JSON complet dépliable.

## 8. Sécurité et garde-fous

`app/ai/security.py::analyser_securite` détecte, sur la description du ticket :

- des **tentatives d'injection de prompt** (« ignore tes instructions », « désactive la sécurité », etc.) ;
- des **demandes d'actions sensibles** (réinitialisation de mot de passe, modification de droits, incident de
  cybersécurité) ;
- la présence de **données personnelles** (adresse courriel, numéro de téléphone) dans le texte.

Conséquences dans l'agent :
- une injection détectée bloque toute résolution automatique → `action = "escalade"`, aucune action sensible
  n'est exécutée, le motif est tracé dans le ticket (`raison_escalade`) ;
- une catégorie Cybersécurité, une priorité Haute/Critique ou une confiance faible imposent systématiquement
  `validation_humaine_requise = true` ;
- toutes ces décisions sont journalisées et consultables dans le tableau de bord d'observabilité.

## 9. Stratégie d'évaluation

`tests/test_scenarios.py` exécute directement l'agent (sans passer par HTTP) sur les 4 scénarios obligatoires du
sujet (section 8), avec une assertion propre à chaque scénario (catégorie/priorité attendue, présence de sources,
détection d'informations manquantes, détection de l'injection). Les résultats détaillés (entrée, sortie complète,
réussite/échec) sont exportés dans `data/evaluation_results.json` pour analyse. Cette approche est volontairement
simple et reproductible ; elle pourrait être étendue avec un jeu de tickets plus large et des métriques de
précision/rappel par catégorie si un historique de tickets étiquetés était disponible.

## 10. Limites connues

- Classification par mots-clés, non robuste aux synonymes, fautes d'orthographe importantes ou formulations très
  indirectes.
- RAG par TF-IDF (pas d'embeddings sémantiques) : deux formulations très différentes mais synonymes peuvent
  obtenir un score faible.
- Base d'utilisateurs, d'équipements et de services simulée (fichiers JSON), pas de vraie base de données.
- Détection de sécurité par liste de mots-clés : contournable par reformulation habile ; à renforcer avec un
  modèle de détection dédié dans une version future.
- Pas d'authentification sur l'API (hors périmètre du prototype de hackathon).
