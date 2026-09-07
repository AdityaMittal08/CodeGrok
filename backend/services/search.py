from db import get_connection
from services.embedding import embed_text

def search_chunks(query: str, ast_type: str = None, limit: int = 10, repo_id: int = None) -> list[dict]:
    query_embedding = embed_text(query)
    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT id, file_path, function_name, ast_type, start_line, end_line, code_text,
               1 - (embedding <=> %s::vector) AS similarity
        FROM chunks
    """
    params = [query_embedding]
    filters = []

    if repo_id is not None:
        filters.append("repo_id = %s")
        params.append(repo_id)

    if ast_type:
        filters.append("ast_type = %s")
        params.append(ast_type)

    if filters:
        sql += " WHERE " + " AND ".join(filters)

    sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
    params.extend([query_embedding, limit])

    cur.execute(sql, params)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results