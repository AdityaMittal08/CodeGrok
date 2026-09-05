from fastapi import APIRouter
from pydantic import BaseModel
from services.ingestion import ingest_repo

router = APIRouter()

class IngestRequest(BaseModel):
    repoPath: str
    repoName: str

@router.post("/api/ingest")
def ingest(req: IngestRequest):
    return ingest_repo(req.repoPath, req.repoName)