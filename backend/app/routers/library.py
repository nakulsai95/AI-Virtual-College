"""The Library / content knowledge base — retrieved materials + authored lessons."""
from __future__ import annotations

from fastapi import APIRouter

from .. import repo, retrieval
from ..auth import CurrentUser
from ..schemas import SearchIn

router = APIRouter(prefix="/api", tags=["library"])


@router.get("/library")
def library(user=CurrentUser):
    uid = user["id"]
    return {"materials": repo.list_materials(uid), "lessons": repo.list_library(uid)}


@router.post("/materials/search")
def search_materials(body: SearchIn, user=CurrentUser):
    """Ad-hoc retrieval for a topic; results are added to the user's KB."""
    uid = user["id"]
    found = retrieval.gather(body.query, search_config=repo.get_search(uid), n=body.n)
    if found:
        repo.add_materials(uid, body.query, found)
    return {"results": found}
