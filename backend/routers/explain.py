from fastapi import APIRouter, Depends
from fastapi import HTTPException
from pydantic import BaseModel, Field
from security import require_api_key
from services.explanation import explain_match

router = APIRouter()

class ExplainRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    code_text: str = Field(min_length=1, max_length=200_000)
    function_name: str = Field(min_length=1, max_length=200)
    similarity: float = Field(ge=0, le=1)

@router.post("/api/explain")
def explain(req: ExplainRequest, _: None = Depends(require_api_key)):
    try:
        explanation = explain_match(req.query, req.code_text, req.function_name, req.similarity)
    except Exception as error:
        print(f"Explanation provider error: {type(error).__name__}: {error}")
        raise HTTPException(status_code=503, detail="Explanation service is temporarily unavailable") from error
    return {"explanation": explanation}