from datetime import date
from app.policy import PolicyStore
from app.caller import get_caller

def test_current_certification_policy():
    s = PolicyStore()
    c = get_caller("atlas-employee-01")
    p = s.retrieve("annual certification reimbursement limit", c, date(2026,9,21))
    assert any(x["id"] == "atlas-cert-current" for x in p)

def test_draft_is_not_eligible():
    s = PolicyStore()
    c = get_caller("atlas-employee-01")
    p = s.retrieve("certification reimbursement", c, date(2026,9,21))
    assert all(x["id"] != "atlas-cert-draft" for x in p)

def test_tenant_isolation():
    s = PolicyStore()
    c = get_caller("atlas-employee-01")
    p = s.retrieve("home office allowance", c, date(2026,9,21))
    assert all(x["tenant"] == "Atlas" for x in p)
