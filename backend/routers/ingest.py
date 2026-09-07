import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from security import require_api_key, validate_allowed_path
from services.ingestion import (
    MAX_GITHUB_FILES,
    RepositoryTooLargeError,
    create_pending_repo,
    get_repo_status,
    ingest_repo,
    ingest_snippet,
    mark_repo_failed,
)

router = APIRouter()

class IngestRequest(BaseModel):
    repoPath: str = Field(min_length=1, max_length=4096)
    repoName: str = Field(min_length=1, max_length=120)


class SnippetIngestRequest(BaseModel):
    code: str = Field(min_length=1, max_length=200_000)
    language: Literal["javascript", "typescript", "tsx"]
    repoName: str = Field(min_length=1, max_length=120)


class GitHubIngestRequest(BaseModel):
    repoUrl: str = Field(min_length=1, max_length=2048)
    repoName: str | None = Field(default=None, max_length=120)


def validate_github_url(repo_url: str) -> tuple[str, str]:
    try:
        parsed = urlparse(repo_url.strip())
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        raise HTTPException(status_code=400, detail="Repository URL must be a public https://github.com/owner/repo URL.")

    if (
        parsed.scheme != "https"
        or hostname != "github.com"
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise HTTPException(status_code=400, detail="Repository URL must be a public https://github.com/owner/repo URL.")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Repository URL must include exactly an owner and repository name.")
    owner, repo = parts
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not owner or not repo or any(not char.isalnum() and char not in "-_." for char in owner + repo):
        raise HTTPException(status_code=400, detail="Repository URL contains an invalid GitHub owner or repository name.")

    return f"https://github.com/{owner}/{repo}.git", f"{owner}/{repo}"


def ingest_github_repo(repo_id: int, repo_url: str, repo_name: str) -> None:
    clone_dir = tempfile.mkdtemp(prefix="codegrok-github-")
    try:
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, clone_dir],
                check=True,
                timeout=60,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("GitHub clone timed out after 60 seconds. Try a smaller repository.")
        except subprocess.CalledProcessError:
            raise RuntimeError("GitHub could not clone this public repository. Check that the URL is valid and accessible.")

        ingest_repo(
            clone_dir,
            repo_name,
            repo_id=repo_id,
            max_files=MAX_GITHUB_FILES,
            record_source_path=repo_url,
            relative_file_paths=True,
        )
    except RepositoryTooLargeError:
        mark_repo_failed(repo_id, f"Repository is too large. Limit GitHub imports to {MAX_GITHUB_FILES} supported source files.")
    except Exception as error:
        mark_repo_failed(repo_id, str(error) or "Repository indexing failed.")
    finally:
        shutil.rmtree(clone_dir, ignore_errors=True)

@router.post("/api/ingest")
def ingest(req: IngestRequest, _: None = Depends(require_api_key)):
    repo_path = validate_allowed_path(Path(req.repoPath))
    if not repo_path.exists():
        raise HTTPException(status_code=400, detail=f"Repository path does not exist: {req.repoPath}")
    if not repo_path.is_dir() and repo_path.suffix.lower() not in {'.js', '.jsx', '.ts', '.tsx'}:
        raise HTTPException(status_code=400, detail="Repository path must be a source directory or JavaScript/TypeScript file")

    return ingest_repo(str(repo_path), req.repoName)


@router.post("/api/ingest/snippet")
def ingest_snippet_route(req: SnippetIngestRequest, _: None = Depends(require_api_key)):
    if not req.code.strip():
        raise HTTPException(status_code=400, detail="Snippet code cannot be empty")
    result = ingest_snippet(req.code, req.language, req.repoName)
    return {"repo_id": result["repo_id"], "total_chunks": result["total_chunks"]}


@router.post("/api/ingest/github")
def ingest_github(
    req: GitHubIngestRequest,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_api_key),
):
    clone_url, derived_name = validate_github_url(req.repoUrl)
    repo_name = req.repoName.strip() if req.repoName and req.repoName.strip() else derived_name
    repo_id = create_pending_repo(repo_name, clone_url)
    background_tasks.add_task(ingest_github_repo, repo_id, clone_url, repo_name)
    return {"repo_id": repo_id, "total_chunks": 0}


@router.get("/api/repos/{repo_id}/status")
def repo_status(repo_id: int, _: None = Depends(require_api_key)):
    result = get_repo_status(repo_id)
    if not result:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return {
        "repo_id": result["id"],
        "status": result["status"],
        "total_chunks": result["total_chunks"],
        "detail": result["failure_message"],
    }
