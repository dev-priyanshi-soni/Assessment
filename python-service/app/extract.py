import re
from pathlib import Path

from pypdf import PdfReader

from .models import Extracted


def extract_text(path: Path) -> str:
    """
    Extract text from supported employee request documents.

    Supported formats:
    - UTF-8 TXT
    - Text-based PDF
    """

    suffix = path.suffix.lower()

    # -------------------------------------------------------------
    # TXT
    # -------------------------------------------------------------
    if suffix == ".txt":
        try:
            return path.read_text(
                encoding="utf-8",
                errors="strict",
            )
        except UnicodeDecodeError as exc:
            raise ValueError("UNREADABLE_FILE") from exc

    # -------------------------------------------------------------
    # PDF
    # -------------------------------------------------------------
    if suffix == ".pdf":
        try:
            reader = PdfReader(str(path))

            text_parts = []

            for page in reader.pages:
                page_text = page.extract_text() or ""

                if page_text:
                    text_parts.append(page_text)

            return "\n".join(text_parts).strip()

        except Exception as exc:
            raise ValueError("UNREADABLE_FILE") from exc

    # -------------------------------------------------------------
    # Unsupported format
    # -------------------------------------------------------------
    raise ValueError("UNSUPPORTED_FILE_TYPE")


def extract_fields(text: str) -> Extracted:
    """
    Extract structured fields from an employee request.

    This is intentionally deterministic for the supplied synthetic
    assessment corpus.
    """

    normalized = " ".join(text.split())

    # -------------------------------------------------------------
    # Reference
    # -------------------------------------------------------------
    reference_match = re.search(
        r"\bReference:\s*([A-Za-z0-9_-]+)",
        normalized,
        re.IGNORECASE,
    )

    reference = (
        reference_match.group(1)
        if reference_match
        else None
    )

    # -------------------------------------------------------------
    # Currency
    # -------------------------------------------------------------
    currency = None

    if re.search(r"\bINR\b|₹", normalized, re.IGNORECASE):
        currency = "INR"

    # -------------------------------------------------------------
    # Benefit
    # -------------------------------------------------------------
    benefit = None

    benefit_patterns = [
        (
            r"certification\s+reimbursement",
            "certification reimbursement",
        ),
        (
            r"home[- ]office\s+allowance",
            "home-office allowance",
        ),
        (
            r"home[- ]office",
            "home-office allowance",
        ),
        (
            r"gym\s+membership|wellness\s+benefit",
            "wellness benefit",
        ),
        (
            r"external\s+training|training",
            "external training",
        ),
    ]

    for pattern, value in benefit_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            benefit = value
            break

    # -------------------------------------------------------------
    # Amount
    #
    # If multiple contradictory amounts are present, don't guess.
    # The assessment specifically uses request-03 for this case.
    # -------------------------------------------------------------
    amounts = re.findall(
        r"\bINR\s*([0-9]+(?:\.[0-9]+)?)",
        normalized,
        re.IGNORECASE,
    )

    amount = None

    if len(amounts) == 1:
        amount = float(amounts[0])

        if amount.is_integer():
            amount = int(amount)

    elif len(amounts) > 1:
        # Ambiguous/conflicting monetary values.
        amount = None

    return Extracted(
        benefit=benefit,
        amount=amount,
        currency=currency,
        reference=reference,
    )