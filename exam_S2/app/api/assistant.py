from fastapi import APIRouter

from app.ai.agent import traiter_ticket
from app.models.schemas import TicketCreate

router = APIRouter(prefix="/api/assistant", tags=["Assistant"])


@router.post("/analyser")
def analyser_ticket(ticket: TicketCreate):
    resultat = traiter_ticket(
        utilisateur_id=ticket.utilisateur_id,
        description=ticket.description,
        equipement_id=ticket.equipement_id,
    )
    return resultat
