from services.chunker import extract_chunks

with open('test-sample.ts', 'r') as f:
    code = f.read()

chunks = extract_chunks(code, 'test-sample.ts')
import json
print(json.dumps(chunks, indent=2))