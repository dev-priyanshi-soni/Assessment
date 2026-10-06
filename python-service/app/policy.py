import json
from datetime import date
from pathlib import Path
import numpy as np
import faiss
from .config import POLICY_PATH
from .models import Caller, Citation

# Deterministic local embedding: hashed token vectors. No network/API key required.
DIM = 384

def embed(text: str) -> np.ndarray:
    v = np.zeros(DIM, dtype="float32")
    for token in text.lower().split():
        h = hash(token) % DIM
        v[h] += 1.0
    norm = np.linalg.norm(v)
    return v / norm if norm else v

class PolicyStore:
    def __init__(self, path: Path = POLICY_PATH):
        self.policies = json.loads(path.read_text(encoding="utf-8"))
        self.index = faiss.IndexFlatIP(DIM)
        matrix = np.vstack([embed(p["text"]) for p in self.policies]).astype("float32")
        self.index.add(matrix)

    @staticmethod
    def eligible(p, caller: Caller, as_of: date) -> bool:
        return (
            p["tenant"] == caller.tenant
            and p["role"] == caller.role
            and p["approval_state"] == "Approved"
            and date.fromisoformat(p["effective_from"]) <= as_of < date.fromisoformat(p["effective_to"])
        )

    @staticmethod
    def benefit(text: str) -> str | None:
        lower = text.lower()
        if "certification" in lower:
            return "certification reimbursement"
        if "home-office" in lower or "home office" in lower:
            return "home-office allowance"
        if "training" in lower:
            return "external training"
        if "gym" in lower or "wellness" in lower:
            return "wellness benefit"
        if "rail" in lower or "travel" in lower:
            return "travel"
        return None

    def retrieve(self, question: str, caller: Caller, as_of: date, k: int = 8):
        q = embed(question).reshape(1, -1)
        _, ids = self.index.search(q, min(k, len(self.policies)))
        candidates = [self.policies[int(i)] for i in ids[0] if i >= 0]
        question_benefit = self.benefit(question)
        eligible = [
            p for p in candidates
            if self.eligible(p, caller, as_of)
            and (question_benefit is None or self.benefit(p["text"]) == question_benefit)
        ]
        # A small corpus is intentionally filtered deterministically after semantic candidate retrieval.
        return eligible

    def citations(self, policies):
        return [Citation(chunk_id=p["id"], quote=p["text"]) for p in policies]
