from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Literal, Optional
from security import require_api_key
from services.search import search_chunks

router = APIRouter()

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    astType: Optional[Literal["function_declaration", "method_definition", "arrow_function"]] = None
    limit: int = Field(default=10, ge=1, le=50)

@router.post("/api/search")
def search(req: SearchRequest, _: None = Depends(require_api_key)):
    return search_chunks(req.query, req.astType, req.limit)