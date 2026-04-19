from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.tools.review_skillgen.adversarial_review_contract import (
    ADVERSARIAL_REVIEW_REQUEST_FILENAME,
    SPAWNED_REVIEWER_RECEIPT_FILENAME,
    validate_receipt_against_request,
    validate_result_against_request,
)
from runtime.tools.review_skillgen.reviewer_write_scope_audit import (
    REVIEWER_WRITE_SCOPE_AUDIT_FILENAME,
    load_reviewer_write_scope_audit,
    validate_reviewer_write_scope_audit,
)
from runtime.tools.review_skillgen.review_result_writer import ensure_runtime_review_result


def load_and_validate_protocol(
    *,
    review_request_dir: Path,
    review_result_dir: Path,
    request_loader: Any,
    receipt_loader: Any,
    runtime_identity: Any,
) -> dict[str, Any]:
    request_path = review_request_dir / ADVERSARIAL_REVIEW_REQUEST_FILENAME
    receipt_path = review_request_dir / SPAWNED_REVIEWER_RECEIPT_FILENAME
    audit_path = review_result_dir / REVIEWER_WRITE_SCOPE_AUDIT_FILENAME

    request_payload = request_loader(request_path)
    receipt_payload = receipt_loader(receipt_path)
    validate_receipt_against_request(
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        runtime_identity=runtime_identity,
    )

    review_result = ensure_runtime_review_result(
        review_result_dir=review_result_dir,
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        runtime_identity=runtime_identity,
    )
    validate_result_against_request(
        request_payload=request_payload,
        receipt_payload=receipt_payload,
        result_payload=review_result,
        runtime_identity=runtime_identity,
    )

    audit_payload = load_reviewer_write_scope_audit(audit_path)
    validate_reviewer_write_scope_audit(
        receipt_payload=receipt_payload,
        audit_payload=audit_payload,
    )

    return {
        "request_payload": request_payload,
        "receipt_payload": receipt_payload,
        "review_result": review_result,
        "audit_payload": audit_payload,
    }
