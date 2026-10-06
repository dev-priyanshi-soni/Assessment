from pathlib import Path

from app.extract import extract_text, extract_fields


def test_extract_txt_file(tmp_path):
    path = tmp_path / "request.txt"

    path.write_text(
        "Reference: CERT-101\n"
        "I request certification reimbursement of INR 18000.",
        encoding="utf-8",
    )

    text = extract_text(path)

    assert "CERT-101" in text
    assert "INR 18000" in text


def test_extract_certification_fields(tmp_path):
    path = tmp_path / "request.txt"

    path.write_text(
        "Reference: CERT-101\n"
        "I request certification reimbursement of INR 18000.",
        encoding="utf-8",
    )

    fields = extract_fields(extract_text(path))

    assert fields.reference == "CERT-101"
    assert fields.benefit == "certification reimbursement"
    assert fields.amount == 18000
    assert fields.currency == "INR"


def test_conflicting_amounts_are_not_guessed(tmp_path):
    path = tmp_path / "request.txt"

    path.write_text(
        "Reference: CERT-303\n"
        "Certification reimbursement request. "
        "The invoice says INR 22000. "
        "My reimbursement form says INR 28000. "
        "Neither amount has been corrected.",
        encoding="utf-8",
    )

    fields = extract_fields(extract_text(path))

    assert fields.reference == "CERT-303"
    assert fields.amount is None
    assert fields.currency == "INR"


def test_request_without_amount(tmp_path):
    path = tmp_path / "request.txt"

    path.write_text(
        "Reference: TRAIN-707\n"
        "I have already booked external training.",
        encoding="utf-8",
    )

    fields = extract_fields(extract_text(path))

    assert fields.reference == "TRAIN-707"
    assert fields.amount is None
    assert fields.benefit == "external training"


def test_unsupported_file_type(tmp_path):
    path = tmp_path / "request.docx"
    path.write_bytes(b"test")

    try:
        extract_text(path)
        assert False, "Expected unsupported file type"
    except ValueError as exc:
        assert str(exc) == "UNSUPPORTED_FILE_TYPE"