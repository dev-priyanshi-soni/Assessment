from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_answer_requires_caller():
    response = client.post(
        "/internal/answer",
        json={
            "question": "What is the certification reimbursement limit?",
            "as_of": "2026-09-21",
        },
    )

    assert response.status_code in (400, 422)


def test_answer_requires_question():
    response = client.post(
        "/internal/answer",
        headers={
            "X-Caller-Id": "atlas-employee-01",
        },
        json={
            "as_of": "2026-09-21",
        },
    )

    assert response.status_code == 422


def test_answer_with_valid_request():
    response = client.post(
        "/internal/answer",
        headers={
            "X-Caller-Id": "atlas-employee-01",
        },
        json={
            "question": (
                "What is the annual certification "
                "reimbursement limit?"
            ),
            "as_of": "2026-09-21",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] in {
        "ANSWERED",
        "INSUFFICIENT_EVIDENCE",
        "CONFLICT",
    }

    assert "citations" in body