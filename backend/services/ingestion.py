from psycopg2.extras import execute_values
from db import get_connection
from services.chunker import extract_chunks
from services.embedding import embed_batch
from utils.file_walker import walk_dir
from services.embedding import embed_batch, BATCH_SIZE


def ingest_repo(repo_path: str, repo_name: str) -> dict:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM repos WHERE name = %s", (repo_name,))
    row = cur.fetchone()

    if row:
        repo_id = row['id']
        cur.execute(
            "UPDATE repos SET source_path = %s, ingested_at = now() WHERE id = %s",
            (repo_path, repo_id)
        )
    else:
        cur.execute(
            "INSERT INTO repos (name, source_path) VALUES (%s, %s) RETURNING id",
            (repo_name, repo_path)
        )
        repo_id = cur.fetchone()['id']

    cur.execute("DELETE FROM chunks WHERE repo_id = %s", (repo_id,))

    files = walk_dir(repo_path)
    print(f"Total files found: {len(files)}")

    # Step 1: parse all files and collect chunks first (no embedding yet)
    all_chunks = []
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

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
        conn.commit()
        cur.close()
        conn.close()
        return {
            "repo_id": repo_id,
            "repo_path": repo_path,
            "files_scanned": len(files),
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

    conn.commit()
    cur.close()
    conn.close()

    total_chunks = len(all_chunks)
    print(f"Ingested {total_chunks} chunks from {len(files)} files")
    return {
        "repo_id": repo_id,
        "repo_path": repo_path,
        "files_scanned": len(files),
        "total_chunks": total_chunks,
    }