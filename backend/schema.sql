CREATE TABLE IF NOT EXISTS repos (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  source_path TEXT,
  ingested_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
  id SERIAL PRIMARY KEY,
  repo_id INTEGER REFERENCES repos(id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  function_name TEXT,
  ast_type TEXT,
  start_line INTEGER,
  end_line INTEGER,
  code_text TEXT NOT NULL,
  embedding vector(384)
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx
  ON chunks USING hnsw (embedding vector_cosine_ops);