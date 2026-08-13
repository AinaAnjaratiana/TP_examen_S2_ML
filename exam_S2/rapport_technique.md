# Rapport technique — mAIntenance & Assistance

## Équipe
_À compléter par l'équipe : noms, rôles._

## 1. Résumé

Le prototype livré est une chaîne complète de traitement de tickets d'assistance informatique : un utilisateur
décrit son problème en langage naturel, l'assistant le classifie, consulte des outils internes, interroge une
base de connaissances (RAG), détecte les informations manquantes et les demandes sensibles/malveillantes, puis
produit une décision structurée (résolution, demande d'information ou escalade), le tout journalisé pour
l'observabilité. Le détail technique complet est dans `README.md`.

## 2. Approche choisie pour analyser et router les tickets

Classification par **règles pondérées sur mots-clés**, sans modèle de Machine Learning entraîné (choix
volontaire — cf. note de cadrage du sujet : « aucun point particulier n'est réservé à l'utilisation d'un modèle
de ML »). Chaque catégorie du sujet (comptes, réseau, matériel, logiciels, imprimantes, droits d'accès,
cybersécurité, autre) est associée à une liste de mots-clés ; la catégorie avec le plus de correspondances est
retenue et la confiance croît avec le nombre de correspondances. La priorité découle de mots signalant
l'urgence, de la catégorie (Cybersécurité → toujours critique) et de la présence d'un incident actif de même
catégorie touchant potentiellement plusieurs utilisateurs.

Ce choix privilégie l'explicabilité totale (chaque décision est justifiable mot-clé par mot-clé) et la rapidité
de mise en œuvre dans le temps du hackathon, au prix d'une robustesse limitée aux formulations non anticipées.

## 3. Fonctionnement du système RAG

Recherche documentaire par **TF-IDF + similarité cosinus**, implémentée en pur Python (aucune dépendance
externe), sur une base de connaissances de 8 fichiers texte (`data/knowledge/`) couvrant comptes, réseau,
matériel, imprimantes, logiciels, droits d'accès, cybersécurité et procédures d'escalade. Chaque fichier est
découpé en passages ; chaque requête est comparée à tous les passages et les meilleurs scores au-dessus d'un
seuil de pertinence sont renvoyés comme sources, avec leur score. Si aucune source ne dépasse le seuil, le
système le signale explicitement (`sources: []`) et abaisse la confiance globale, ce qui déclenche une demande
de validation humaine plutôt qu'une réponse hasardeuse.

## 4. Outils accessibles à l'agent

Quatre outils de consultation (`rechercher_utilisateur`, `consulter_equipement`, `verifier_etat_service`,
`rechercher_incidents_actifs`) et quatre outils d'action (`creer_ticket`, `mettre_a_jour_ticket`,
`affecter_ticket`, `escalader_vers_technicien`), tous implémentés dans `app/tools/`. Chaque appel est chronométré
et journalisé (paramètres, résultat, statut, latence) via `app/core/observabilite.py::appeler_outil`. Aucune
action sensible n'est jamais exécutée automatiquement : ces cas sont systématiquement escaladés avec validation
humaine requise.

## 5. Stratégie d'évaluation

`tests/test_scenarios.py` exécute les 4 scénarios obligatoires du sujet directement sur l'agent, avec une
assertion dédiée par scénario, et exporte un rapport détaillé dans `data/evaluation_results.json`
(4/4 scénarios validés lors des tests de développement). Cette approche reproductible peut être étendue avec un
échantillon de tickets plus large pour mesurer précision/rappel par catégorie.

## 6. Mécanismes de sécurité

`app/ai/security.py` détecte, par mots-clés, les tentatives d'injection de prompt, les demandes d'actions
sensibles et la présence de données personnelles dans le texte du ticket. Toute injection détectée bloque
l'exécution automatique et force une escalade avec validation humaine ; il en va de même pour les tickets de
catégorie Cybersécurité ou de priorité Haute/Critique, ainsi que pour toute réponse dont la confiance est
insuffisante. Ces décisions sont tracées dans le ticket (`raison_escalade`) et dans le journal d'observabilité.

## 7. Limites connues

- Classification par mots-clés : peu robuste aux synonymes, fautes d'orthographe importantes, négations.
- RAG lexical (TF-IDF), pas d'embeddings sémantiques.
- Données simulées (fichiers JSON), pas de vraie base de données ni d'authentification.
- Détection de sécurité par liste de mots-clés, contournable par reformulation ; à renforcer dans une version
  future (classifieur dédié, liste de règles plus riche, revue humaine systématique des cas ambigus).

## 8. Pistes d'amélioration

- Remplacer le TF-IDF par des embeddings + base vectorielle pour un RAG sémantique.
- Ajouter un vrai modèle de classification (ML supervisé ou LLM few-shot) en conservant l'interface actuelle.
- Étendre le jeu de tests avec des tickets réels étiquetés pour mesurer la précision par catégorie.
- Ajouter une authentification et une gestion des rôles (utilisateur / technicien / administrateur).
