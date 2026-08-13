from fastapi import APIRouter

from app.tools.utilisateurs import lister_utilisateurs

router = APIRouter(prefix="/api/utilisateurs", tags=["Utilisateurs"])


@router.get("")
def lister():
    return lister_utilisateurs()
