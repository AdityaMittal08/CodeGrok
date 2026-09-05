from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.search import search_chunks

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    astType: Optional[str] = None
    limit: int = 10

@router.post("/api/search")
def search(req: SearchRequest):
    return search_chunks(req.query, req.astType, req.limit)