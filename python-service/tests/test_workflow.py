from datetime import date
from app.policy import PolicyStore
from app.workflow import AnswerWorkflow
from app.caller import get_caller

def test_answered():
    w = AnswerWorkflow(PolicyStore())
    r = w.run("What is my annual certification reimbursement limit?", date(2026,9,21), get_caller("atlas-employee-01"))
    assert r.status == "ANSWERED"
    assert any(c.chunk_id == "atlas-cert-current" for c in r.citations)

def test_home_office_conflict():
    w = AnswerWorkflow(PolicyStore())
    r = w.run("What is my annual home-office allowance?", date(2026,9,21), get_caller("atlas-employee-01"))
    assert r.status == "CONFLICT"

def test_insufficient():
    w = AnswerWorkflow(PolicyStore())
    r = w.run("What is my wellness benefit?", date(2026,9,21), get_caller("atlas-employee-01"))
    assert r.status == "INSUFFICIENT_EVIDENCE"
