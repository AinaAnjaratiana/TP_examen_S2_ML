from fastapi import APIRouter, HTTPException

from app.tools.tickets import obtenir_ticket, obtenir_tickets

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


@router.get("")
def lister_tickets():
    return obtenir_tickets()


@router.get("/{ticket_id}")
def lire_ticket(ticket_id: int):
    ticket = obtenir_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket introuvable")
    return ticket
