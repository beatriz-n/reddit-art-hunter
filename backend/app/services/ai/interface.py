from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AnalysisRequest:
    title: str
    body: str
    image_urls: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnalysisResult:
    intent_to_commission: bool
    summary: str
    confidence: float


class OpportunityAnalyzer(Protocol):
    """Contract for a future local text and image model adapter."""

    async def analyze(self, request: AnalysisRequest) -> AnalysisResult: ...
