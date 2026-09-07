from pathlib import Path

from psycopg2.extras import execute_values
from db import get_connection
from services.chunker import extract_chunks
from utils.file_walker import walk_dir
from services.embedding import embed_batch, BATCH_SIZE


MAX_GITHUB_FILES = 2_000


class RepositoryTooLargeError(ValueError):
    pass


def _ingest_sources(
    repo_name: str,
    source_path: str,
    sources: list[tuple[str, str]],
    files_scanned: int,
    repo_id: int | None = None,
) -> dict:
    conn = get_connection()
    cur = conn.cursor()

    try:
        if repo_id is None:
            cur.execute("SELECT id FROM repos WHERE name = %s", (repo_name,))
            row = cur.fetchone()

            if row:
                repo_id = row['id']
                cur.execute(
                    "UPDATE repos SET source_path = %s, ingested_at = now(), status = 'ready', failure_message = NULL WHERE id = %s",
                    (source_path, repo_id)
                )
            else:
                cur.execute(
                    "INSERT INTO repos (name, source_path, status) VALUES (%s, %s, 'ready') RETURNING id",
                    (repo_name, source_path)
                )
                repo_id = cur.fetchone()['id']
        else:
            cur.execute(
                "UPDATE repos SET source_path = %s, ingested_at = now(), status = 'pending', failure_message = NULL WHERE id = %s",
                (source_path, repo_id),
            )

        cur.execute("DELETE FROM chunks WHERE repo_id = %s", (repo_id,))

        print(f"Total files found: {files_scanned}")

        # Step 1: parse all files and collect chunks first (no embedding yet)
        all_chunks = []
        for file_path, code in sources:
            if len(code) > 200_000:
                print(f"Skipping {file_path}: too large")
                continue

            try:
                chunks = extract_chunks(code, file_path)
            except Exception as e:
                print(f"Skipping {file_path}: parse error - {e}")
                continue

            all_chunks.extend(chunks)

        print(f"Total chunks extracted: {len(all_chunks)}")

        if not all_chunks:
            cur.execute("UPDATE repos SET status = 'ready' WHERE id = %s", (repo_id,))
            conn.commit()
            return {
                "repo_id": repo_id,
                "repo_path": source_path,
                "files_scanned": files_scanned,
                "total_chunks": 0,
            }

        # Step 2: embed all chunks in batches (much faster than one at a time)

        all_embeddings = []
        for i in range(0, len(all_chunks), BATCH_SIZE):
            batch_texts = [c['code_text'] for c in all_chunks[i:i + BATCH_SIZE]]
            batch_embeddings = embed_batch(batch_texts)
            all_embeddings.extend(batch_embeddings)
            print(f"Embedded {min(i + BATCH_SIZE, len(all_chunks))}/{len(all_chunks)} chunks")

        # Step 3: bulk insert everything in one query
        rows = [
            (
                repo_id,
                chunk['file_path'],
                chunk['function_name'],
                chunk['ast_type'],
                chunk['start_line'],
                chunk['end_line'],
                chunk['code_text'],
                embedding,
            )
            for chunk, embedding in zip(all_chunks, all_embeddings)
        ]

        execute_values(
            cur,
            """INSERT INTO chunks (repo_id, file_path, function_name, ast_type, start_line, end_line, code_text, embedding)
               VALUES %s""",
            rows,
        )

        cur.execute("UPDATE repos SET status = 'ready', failure_message = NULL WHERE id = %s", (repo_id,))
        conn.commit()

        total_chunks = len(all_chunks)
        print(f"Ingested {total_chunks} chunks from {files_scanned} files")
        return {
            "repo_id": repo_id,
            "repo_path": source_path,
            "files_scanned": files_scanned,
            "total_chunks": total_chunks,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def ingest_repo(
    repo_path: str,
    repo_name: str,
    repo_id: int | None = None,
    max_files: int | None = None,
    record_source_path: str | None = None,
    relative_file_paths: bool = False,
) -> dict:
    files = walk_dir(repo_path)
    if max_files is not None and len(files) > max_files:
        raise RepositoryTooLargeError(
            f"Repository is too large: found more than {max_files} supported source files."
        )
    sources = []
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            stored_file_path = (
                str(Path(file_path).relative_to(Path(repo_path)))
                if relative_file_paths
                else file_path
            )
            sources.append((stored_file_path, f.read()))
    return _ingest_sources(
        repo_name,
        record_source_path or repo_path,
        sources,
        len(files),
        repo_id=repo_id,
    )


def ingest_snippet(code: str, language: str, repo_name: str) -> dict:
    extension = {"javascript": "js", "typescript": "ts", "tsx": "tsx"}[language]
    file_path = f"pasted-snippet.{extension}"
    return _ingest_sources(repo_name, file_path, [(file_path, code)], 1)


def create_pending_repo(repo_name: str, repo_url: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    try:
        candidate_name = repo_name
        suffix = 2
        while True:
            cur.execute("SELECT 1 FROM repos WHERE name = %s", (candidate_name,))
            if not cur.fetchone():
                break
            candidate_name = f"{repo_name} ({suffix})"
            suffix += 1

        cur.execute(
            "INSERT INTO repos (name, source_path, status) VALUES (%s, %s, 'pending') RETURNING id",
            (candidate_name, repo_url),
        )
        repo_id = cur.fetchone()['id']
        conn.commit()
        return repo_id
    finally:
        cur.close()
        conn.close()


def mark_repo_failed(repo_id: int, message: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE repos SET status = 'failed', failure_message = %s WHERE id = %s",
            (message[:500], repo_id),
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def get_repo_status(repo_id: int) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT repos.id, repos.status, repos.failure_message, COUNT(chunks.id) AS total_chunks
               FROM repos LEFT JOIN chunks ON chunks.repo_id = repos.id
               WHERE repos.id = %s GROUP BY repos.id""",
            (repo_id,),
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()
