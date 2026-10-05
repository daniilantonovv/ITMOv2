from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, field_validator

from app.llm import LLMTimeout, LLMUnavailable, OllamaLLM, ReviewLLM

MAX_DIFF_CHARS = 20_000

app = FastAPI(title="AI Review API")


class ReviewRequest(BaseModel):
    diff: str

    @field_validator("diff")
    @classmethod
    def diff_not_blank(cls, diff: str) -> str:
        if not diff.strip():
            raise ValueError("diff must not be empty")
        return diff


class ReviewResponse(BaseModel):
    review: str


def get_llm() -> ReviewLLM:
    return OllamaLLM()


@app.post("/review", response_model=ReviewResponse)
def review(request: ReviewRequest, llm: ReviewLLM = Depends(get_llm)) -> ReviewResponse:
    # Size is checked here, not with Field(max_length=...): the contract wants 413, not 422.
    if len(request.diff) > MAX_DIFF_CHARS:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"diff too large: max {MAX_DIFF_CHARS} characters",
        )
    # Error details stay in the server; the client only gets the contract text.
    try:
        answer = llm.review(request.diff)
    except LLMTimeout as error:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, detail="LLM timeout") from error
    except LLMUnavailable as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail="LLM unavailable") from error
    return ReviewResponse(review=answer)
