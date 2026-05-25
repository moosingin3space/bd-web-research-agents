from pydantic import BaseModel, Field


class Citation(BaseModel):
    url: str = Field(description="Source URL.")
    title: str = Field(description="Human-readable source title when available.")
    quote_or_evidence: str = Field(
        description="Short paraphrase or brief evidence snippet supporting a claim."
    )


class ResearchClaim(BaseModel):
    claim: str
    confidence: str = Field(description="low, medium, or high")
    citations: list[Citation]


class ResearchReport(BaseModel):
    question: str
    answer: str
    key_findings: list[ResearchClaim]
    open_questions: list[str] = Field(
        description="Important unknowns, contradictions, or areas needing paid/private data."
    )
    sources_consulted: list[Citation]
