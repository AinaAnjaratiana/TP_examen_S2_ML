"""Système de recherche documentaire (RAG) sur la base de connaissances
data/knowledge/*.txt.

Approche : chaque fichier est découpé en passages (paragraphes séparés par une
ligne vide). Un index TF-IDF est construit en pur Python (aucune dépendance
externe requise), puis la similarité cosinus entre la requête et chaque
passage permet de retrouver les extraits les plus pertinents et d'y associer
un score de confiance. C'est une première version volontairement simple par
mots-clés pondérés ; elle pourra être remplacée plus tard par des embeddings
et une base vectorielle sans changer l'interface `rechercher_dans_base`.
"""

import math
import re
from collections import Counter
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "data" / "knowledge"

MOTS_VIDES = {
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "est",
    "sont", "au", "aux", "ce", "ces", "cet", "cette", "en", "dans", "sur",
    "pour", "par", "avec", "sans", "que", "qui", "ne", "pas", "il", "elle",
    "vous", "nous", "je", "tu", "son", "sa", "ses", "leur", "leurs", "être",
    "avoir", "plus", "peut", "doit", "afin", "puis", "avant", "après", "si",
}


def _tokenize(texte):
    texte = texte.lower()
    texte = re.sub(r"[^a-zàâäéèêëïîôöùûüçñ0-9\s]", " ", texte)
    return [mot for mot in texte.split() if len(mot) > 2 and mot not in MOTS_VIDES]


class IndexDocumentaire:
    def __init__(self):
        self.passages = []
        self.idf = {}
        self._charger_passages()
        self._calculer_idf()

    def _charger_passages(self):
        if not KNOWLEDGE_DIR.exists():
            return

        for fichier in sorted(KNOWLEDGE_DIR.glob("*.txt")):
            contenu = fichier.read_text(encoding="utf-8")
            blocs = [bloc.strip() for bloc in contenu.split("\n\n") if bloc.strip()]

            for index, bloc in enumerate(blocs):
                titre = bloc.split("\n", 1)[0]
                self.passages.append(
                    {
                        "id": f"{fichier.stem}-{index + 1}",
                        "document": fichier.name,
                        "titre": titre,
                        "texte": bloc,
                        "tokens": _tokenize(bloc),
                    }
                )

    def _calculer_idf(self):
        n = len(self.passages) or 1
        occurrences = Counter()

        for passage in self.passages:
            for terme in set(passage["tokens"]):
                occurrences[terme] += 1

        self.idf = {
            terme: math.log((n + 1) / (freq + 1)) + 1
            for terme, freq in occurrences.items()
        }

    def _vecteur(self, tokens):
        if not tokens:
            return {}
        tf = Counter(tokens)
        total = len(tokens)
        return {
            terme: (compte / total) * self.idf.get(terme, 1.0)
            for terme, compte in tf.items()
        }

    @staticmethod
    def _similarite_cosinus(v1, v2):
        termes_communs = set(v1) & set(v2)
        if not termes_communs:
            return 0.0

        produit_scalaire = sum(v1[t] * v2[t] for t in termes_communs)
        norme1 = math.sqrt(sum(v * v for v in v1.values()))
        norme2 = math.sqrt(sum(v * v for v in v2.values()))

        if norme1 == 0 or norme2 == 0:
            return 0.0

        return produit_scalaire / (norme1 * norme2)

    def rechercher(self, requete, top_k=3, seuil=0.05):
        tokens_requete = _tokenize(requete)
        if not tokens_requete:
            return []

        vecteur_requete = self._vecteur(tokens_requete)
        resultats = []

        for passage in self.passages:
            vecteur_passage = self._vecteur(passage["tokens"])
            score = self._similarite_cosinus(vecteur_requete, vecteur_passage)

            if score > 0:
                resultats.append(
                    {
                        "id": passage["id"],
                        "document": passage["document"],
                        "titre": passage["titre"],
                        "extrait": passage["texte"],
                        "score": round(score, 4),
                    }
                )

        resultats.sort(key=lambda r: r["score"], reverse=True)
        pertinents = [r for r in resultats if r["score"] >= seuil]

        return pertinents[:top_k]


_index = None


def _obtenir_index():
    global _index
    if _index is None:
        _index = IndexDocumentaire()
    return _index


def rechercher_dans_base(requete, top_k=3, seuil=0.05):
    """Interface publique du RAG : renvoie une liste de passages pertinents
    (id, document, titre, extrait, score) triés par score décroissant. Une
    liste vide signifie qu'aucune source suffisamment pertinente n'a été
    trouvée — l'agent doit alors signaler une réponse incertaine."""
    return _obtenir_index().rechercher(requete, top_k=top_k, seuil=seuil)
