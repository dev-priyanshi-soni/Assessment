from .models import AnswerResponse, Citation

class OfflineModel:
    """Deterministic model double required by the assessment."""
    def answer(self, question: str, citations: list[Citation]) -> AnswerResponse:
        if not citations:
            return AnswerResponse(status="INSUFFICIENT_EVIDENCE", answer=None, citations=[])
        return AnswerResponse(
            status="ANSWERED",
            answer="Supported by the eligible policy evidence: " + " ".join(c.quote for c in citations),
            citations=citations,
        )
