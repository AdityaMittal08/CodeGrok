import torch
import transformers
from transformers import PretrainedConfig
from sentence_transformers import SentenceTransformer

# 1. Patch the internal helper
if not hasattr(transformers.pytorch_utils, "find_pruneable_heads_and_indices"):
    def find_pruneable_heads_and_indices(heads, n_heads, head_size, already_pruned_heads):
        mask = torch.ones(n_heads, head_size)
        heads = set(heads) - already_pruned_heads
        for head in heads:
            head = head - sum(1 if h < head else 0 for h in already_pruned_heads)
            mask[head] = 0
        mask = mask.view(-1).contiguous().eq(1)
        index = torch.arange(len(mask))[mask].long()
        return heads, index

    transformers.pytorch_utils.find_pruneable_heads_and_indices = find_pruneable_heads_and_indices

# 2. Patch the missing attribute
PretrainedConfig.is_decoder = False
PretrainedConfig.add_cross_attention = False

_model = None

# Keep this as your single source of truth for batch size —
# both single and batch embedding paths respect it.
BATCH_SIZE = 4

def get_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = SentenceTransformer(
            'jinaai/jina-embeddings-v2-base-code',
            trust_remote_code=True,
            model_kwargs={"torch_dtype": torch.float16},
            device=device,
        )
        _model.max_seq_length = 512
        print(f"Embedding model loaded on: {device}")
    return _model

def embed_text(text: str) -> list[float]:
    model = get_model()
    with torch.no_grad():
        embedding = model.encode(text, batch_size=BATCH_SIZE, normalize_embeddings=True)
    return embedding.tolist()

def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = get_model()
    with torch.no_grad():
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=BATCH_SIZE,   # stays at 4 — matches your VRAM-safe config
            show_progress_bar=True,
        )
    if torch.cuda.is_available():
        torch.cuda.empty_cache()   # release freed VRAM back after each batch call
    return embeddings.tolist()