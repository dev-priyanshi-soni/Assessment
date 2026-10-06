import hashlib
from pathlib import Path

from .extract import extract_text, extract_fields
from .workflow import AnswerWorkflow
from .models import BatchResult


class BatchProcessor:
    """
    Orchestrates batch document processing.

    Responsibilities:
    - Validate that manifest files exist
    - Detect exact duplicate files
    - Extract document text
    - Extract structured fields
    - Retrieve/evaluate applicable policy
    - Isolate failures at document level
    - Produce one BatchResult per manifest entry
    """

    def __init__(self, workflow: AnswerWorkflow):
        self.workflow = workflow

    def process(self, files: dict[str, Path], metadata, caller):
        results = []
        hashes = {}

        for entry in metadata.documents:
            path = files.get(entry.filename)

            # ---------------------------------------------------------
            # 1. Manifest file missing
            # ---------------------------------------------------------
            if path is None:
                results.append(
                    BatchResult(
                        document_id=entry.document_id,
                        processing_status="FAILED",
                        review_required=True,
                        issues=["MISSING_FILE_PART"],
                        error={
                            "code": "MISSING_FILE_PART",
                            "message": "Required file part was not supplied.",
                        },
                    )
                )
                continue

            try:
                # -----------------------------------------------------
                # 2. Read bytes and detect empty document
                # -----------------------------------------------------
                raw_bytes = path.read_bytes()

                if len(raw_bytes) == 0:
                    results.append(
                        BatchResult(
                            document_id=entry.document_id,
                            processing_status="FAILED",
                            review_required=True,
                            issues=["TECHNICAL_FAILURE"],
                            error={
                                "code": "EMPTY_FILE",
                                "message": "The item could not be processed safely.",
                            },
                        )
                    )
                    continue

                # -----------------------------------------------------
                # 3. Exact duplicate detection
                # -----------------------------------------------------
                digest = hashlib.sha256(raw_bytes).hexdigest()

                if digest in hashes:
                    results.append(
                        BatchResult(
                            document_id=entry.document_id,
                            processing_status="COMPLETED",
                            extracted=None,
                            field_evidence={},
                            policy=None,
                            review_required=True,
                            issues=["EXACT_DUPLICATE_FILE"],
                            duplicate_of=hashes[digest],
                            error=None,
                        )
                    )
                    continue

                hashes[digest] = entry.document_id

                # -----------------------------------------------------
                # 4. Extract document text
                #
                # extract_text() supports:
                # - UTF-8 TXT
                # - text-based PDF
                # -----------------------------------------------------
                text = extract_text(path)

                if not text.strip():
                    results.append(
                        BatchResult(
                            document_id=entry.document_id,
                            processing_status="FAILED",
                            review_required=True,
                            issues=["TECHNICAL_FAILURE"],
                            error={
                                "code": "EMPTY_FILE",
                                "message": "The item could not be processed safely.",
                            },
                        )
                    )
                    continue

                # -----------------------------------------------------
                # 5. Extract structured fields
                # -----------------------------------------------------
                extracted = extract_fields(text)

                issues = []

                if extracted.amount is None:
                    issues.append("AMOUNT_MISSING_OR_AMBIGUOUS")

                if extracted.benefit is None:
                    issues.append("BENEFIT_MISSING_OR_UNRESOLVED")

                # -----------------------------------------------------
                # 6. Policy evaluation
                #
                # The request document is NOT added to the KB.
                # The workflow queries the existing policy KB using:
                # caller + benefit + as_of date.
                # -----------------------------------------------------
                policy = None

                if extracted.benefit:
                    policy = self.workflow.run(
                        f"What policy applies to the {extracted.benefit}?",
                        metadata.as_of,
                        caller,
                    )

                    if policy.status == "CONFLICT":
                        issues.append("POLICY_CONFLICT")

                # -----------------------------------------------------
                # 7. Successful document processing
                # -----------------------------------------------------
                results.append(
                    BatchResult(
                        document_id=entry.document_id,
                        processing_status="COMPLETED",
                        extracted=extracted,
                        field_evidence={},
                        policy=policy,
                        review_required=True,
                        issues=issues or ["HUMAN_REVIEW_REQUIRED"],
                        duplicate_of=None,
                        error=None,
                    )
                )

            # ---------------------------------------------------------
            # 8. Isolate technical failure to this document
            # ---------------------------------------------------------
            except Exception as exc:
                error_code = (
                    str(exc)
                    if str(exc) in {
                        "EMPTY_FILE",
                        "UNREADABLE_FILE",
                        "UNSUPPORTED_FILE_TYPE",
                    }
                    else "ITEM_PROCESSING_FAILURE"
                )

                results.append(
                    BatchResult(
                        document_id=entry.document_id,
                        processing_status="FAILED",
                        review_required=True,
                        issues=["TECHNICAL_FAILURE"],
                        error={
                            "code": error_code,
                            "message": "The item could not be processed safely.",
                        },
                    )
                )

        return results