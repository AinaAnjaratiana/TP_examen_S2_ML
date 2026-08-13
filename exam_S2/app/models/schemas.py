from typing import List, Optional

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    utilisateur_id: int
    description: str
    equipement_id: Optional[int] = None


class Ticket(BaseModel):
    id: int
    utilisateur_id: int
    description: str
    equipement_id: Optional[int] = None
    categorie: Optional[str] = None
    priorite: str = "Moyenne"
    statut: str = "Ouvert"


class Source(BaseModel):
    id: str
    nom: str
    score: float


class ResultatAnalyse(BaseModel):
    """Sortie structurée renvoyée par l'agent (voir cahier des charges, section 5.3)."""

    ticket_id: int
    resume: str
    categorie: str
    priorite: str
    equipe: str
    confiance: float = Field(ge=0, le=1)
    informations_manquantes: List[str] = []
    diagnostic: str
    etapes_resolution: List[str] = []
    questions: List[str] = []
    sources: List[Source] = []
    outils_utilises: List[str] = []
    action: str  # "resolution" | "demande_information" | "escalade"
    validation_humaine_requise: bool
    logs: List[str] = []
