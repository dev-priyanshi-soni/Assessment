from app.batch import BatchProcessor
from app.models import BatchMetadata, BatchDocument, AnswerResponse


class FakeWorkflow:
    def run(self, question, as_of, caller):
        return AnswerResponse(
            status="ANSWERED",
            answer="The annual certification reimbursement limit is INR 25000.",
            citations=[
                {
                    "chunk_id": "test-policy",
                    "quote": (
                        "The annual certification reimbursement "
                        "limit is INR 25000."
                    ),
                }
            ],
        )


class FakeCaller:
    caller_id = "atlas-employee-01"
    tenant = "Atlas"
    role = "employee"


def test_batch_preserves_manifest_order(tmp_path):
    first = tmp_path / "request-01.txt"
    second = tmp_path / "request-02.txt"

    first.write_text(
        "Reference: CERT-101\n"
        "I request certification reimbursement of INR 18000.",
        encoding="utf-8",
    )

    second.write_text(
        "Reference: CERT-102\n"
        "I request certification reimbursement of INR 12000.",
        encoding="utf-8",
    )

    metadata = BatchMetadata(
        batch_id="batch-test",
        as_of="2026-09-21",
        documents=[
            BatchDocument(
                document_id="request-01",
                filename="request-01.txt",
            ),
            BatchDocument(
                document_id="request-02",
                filename="request-02.txt",
            ),
        ],
    )

    results = BatchProcessor(FakeWorkflow()).process(
        {
            "request-01.txt": first,
            "request-02.txt": second,
        },
        metadata,
        FakeCaller(),
    )

    assert [result.document_id for result in results] == [
        "request-01",
        "request-02",
    ]


def test_exact_duplicate_is_detected(tmp_path):
    first = tmp_path / "request-01.txt"
    duplicate = tmp_path / "request-06.txt"

    content = (
        "Reference: CERT-101\n"
        "I request certification reimbursement of INR 18000."
    )

    first.write_text(content, encoding="utf-8")
    duplicate.write_text(content, encoding="utf-8")

    metadata = BatchMetadata(
        batch_id="batch-test",
        as_of="2026-09-21",
        documents=[
            BatchDocument(
                document_id="request-01",
                filename="request-01.txt",
            ),
            BatchDocument(
                document_id="request-06",
                filename="request-06.txt",
            ),
        ],
    )

    results = BatchProcessor(FakeWorkflow()).process(
        {
            "request-01.txt": first,
            "request-06.txt": duplicate,
        },
        metadata,
        FakeCaller(),
    )

    assert results[0].processing_status == "COMPLETED"

    assert results[1].processing_status == "COMPLETED"
    assert results[1].issues == ["EXACT_DUPLICATE_FILE"]
    assert results[1].duplicate_of == "request-01"


def test_empty_file_is_failed(tmp_path):
    empty = tmp_path / "request-08.txt"
    empty.write_bytes(b"")

    metadata = BatchMetadata(
        batch_id="batch-test",
        as_of="2026-09-21",
        documents=[
            BatchDocument(
                document_id="request-08",
                filename="request-08.txt",
            )
        ],
    )

    results = BatchProcessor(FakeWorkflow()).process(
        {"request-08.txt": empty},
        metadata,
        FakeCaller(),
    )

    assert results[0].processing_status == "FAILED"
    assert results[0].error["code"] == "EMPTY_FILE"


def test_missing_file_part_is_failed():
    metadata = BatchMetadata(
        batch_id="batch-test",
        as_of="2026-09-21",
        documents=[
            BatchDocument(
                document_id="request-01",
                filename="missing.txt",
            )
        ],
    )

    results = BatchProcessor(FakeWorkflow()).process(
        {},
        metadata,
        FakeCaller(),
    )

    assert results[0].processing_status == "FAILED"
    assert results[0].error["code"] == "MISSING_FILE_PART"


def test_single_document_processing(tmp_path):
    document = tmp_path / "request.txt"

    document.write_text(
        "Reference: CERT-101\n"
        "I request certification reimbursement of INR 18000.",
        encoding="utf-8",
    )

    metadata = BatchMetadata(
        batch_id="batch-test",
        as_of="2026-09-21",
        documents=[
            BatchDocument(
                document_id="request-01",
                filename="request.txt",
            )
        ],
    )

    results = BatchProcessor(FakeWorkflow()).process(
        {"request.txt": document},
        metadata,
        FakeCaller(),
    )

    result = results[0]

    assert result.processing_status == "COMPLETED"
    assert result.extracted is not None
    assert result.extracted.reference == "CERT-101"
    assert result.extracted.amount == 18000
    assert result.policy is not None