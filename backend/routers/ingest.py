from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from security import require_api_key, validate_allowed_path
from services.ingestion import ingest_repo

router = APIRouter()

class IngestRequest(BaseModel):
    repoPath: str = Field(min_length=1, max_length=4096)
    repoName: str = Field(min_length=1, max_length=120)

@router.post("/api/ingest")
def ingest(req: IngestRequest, _: None = Depends(require_api_key)):
    repo_path = validate_allowed_path(Path(req.repoPath))
    if not repo_path.exists():
        raise HTTPException(status_code=400, detail=f"Repository path does not exist: {req.repoPath}")
    if not repo_path.is_dir() and repo_path.suffix.lower() not in {'.js', '.jsx', '.ts', '.tsx'}:
        raise HTTPException(status_code=400, detail="Repository path must be a source directory or JavaScript/TypeScript file")

    return ingest_repo(str(repo_path), req.repoName)