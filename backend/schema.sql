CREATE TABLE IF NOT EXISTS repos (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  source_path TEXT,
  ingested_at TIMESTAMP DEFAULT now(),
  status TEXT NOT NULL DEFAULT 'ready' CHECK (status IN ('pending', 'ready', 'failed')),
  failure_message TEXT
);

-- Supports databases created before GitHub ingestion was added.
ALTER TABLE repos ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'ready';
ALTER TABLE repos ADD COLUMN IF NOT EXISTS failure_message TEXT;

-- Supports databases created before repository names were made unique.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conrelid = 'repos'::regclass
      AND contype = 'u'
      AND conname = 'repos_name_key'
  ) THEN
    ALTER TABLE repos ADD CONSTRAINT repos_name_key UNIQUE (name);
  END IF;
END
$$;

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
