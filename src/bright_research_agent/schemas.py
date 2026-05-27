from typing import Literal, Optional

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


MovementType = Literal[
    "personnel",
    "product",
    "funding",
    "m_and_a",
    "research",
    "org_change",
    "partnership",
    "regulatory",
]
Bucket = Literal["breaking", "recent", "context"]
Confidence = Literal["low", "medium", "high"]


class Movement(BaseModel):
    organization: str
    movement_type: MovementType
    headline: str
    summary: str
    occurred_on: Optional[str] = Field(
        default=None, description="ISO date or 'around YYYY-MM'."
    )
    surfaced_in: Bucket
    confidence: Confidence
    interestingness: int = Field(ge=1, le=5)
    interestingness_rationale: str
    citations: list[Citation]


class MovementReport(BaseModel):
    run_date: str
    buckets: dict[str, str]
    organizations_checked: list[str]
    movements: list[Movement]
    coverage_gaps: list[str]
    zero_movement_orgs: list[str]
