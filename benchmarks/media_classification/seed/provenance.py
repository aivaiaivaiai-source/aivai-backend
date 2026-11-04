"""Provenance / license audit registry for public seed sources.

checked_at: 2026-08-25
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SourceAudit:
    source_name: str
    official_url: str
    upstream_source: str
    dataset_license: str
    image_content_license: str
    commercial_use: str
    redistribution: str
    derivative_use: str
    provenance_quality: str
    checked_at: str
    verdict: str  # APPROVED_FOR_BENCHMARK | REVIEW_REQUIRED | REJECTED
    notes: str
    download_strategy: str
    estimated_full_bytes: int | None = None
    selective_download: bool = False

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


# --- Audited candidates (3B-2) ---

SOURCE_AUDITS: list[SourceAudit] = [
    SourceAudit(
        source_name="aiomarrehan_vehicles_hf",
        official_url="https://huggingface.co/datasets/AIOmarRehan/Vehicles",
        upstream_source=(
            "Publisher-declared vehicle image collection on HF; "
            "original image capture/rights chain not independently documented"
        ),
        dataset_license="CC0-1.0 (dataset card / README license: cc0-1.0)",
        image_content_license="Publisher claims CC0; upstream per-image rights unclear",
        commercial_use="claimed_yes_via_cc0",
        redistribution="claimed_yes_via_cc0",
        derivative_use="claimed_yes_via_cc0",
        provenance_quality="low_to_medium",
        checked_at="2026-08-25",
        verdict="REVIEW_REQUIRED",
        notes=(
            "CC0 on HF card (~5590 images, 7 classes). "
            "Do not auto-download: CC0 label alone does not prove rights for every upstream image."
        ),
        download_strategy="huggingface_datasets_streaming",
        estimated_full_bytes=872_000_000,
        selective_download=True,
    ),
    SourceAudit(
        source_name="ziya07_multimodal_ecommerce_kaggle",
        official_url="https://www.kaggle.com/datasets/ziya07/multimodal-e-commerce-dataset",
        upstream_source="Kaggle listing; upstream catalog provenance not verified (page often gated)",
        dataset_license="Public metadata previously stated CC0 — not independently re-verified 2026-08-25",
        image_content_license="unclear",
        commercial_use="unclear",
        redistribution="unclear",
        derivative_use="unclear",
        provenance_quality="low",
        checked_at="2026-08-25",
        verdict="REVIEW_REQUIRED",
        notes=(
            "Large (~99k) multimodal set; inefficient for 100–200 seed cases; "
            "provenance not confirmed — no auto-download."
        ),
        download_strategy="kaggle_full_archive",
        estimated_full_bytes=None,
        selective_download=False,
    ),
    SourceAudit(
        source_name="amazon_berkeley_objects_abo",
        official_url="https://registry.opendata.aws/amazon-berkeley-objects/",
        upstream_source="Official Amazon + UC Berkeley ABO (amazon-berkeley-objects S3)",
        dataset_license="CC BY-NC 4.0",
        image_content_license="CC BY-NC 4.0",
        commercial_use="no",
        redistribution="yes_with_attribution_noncommercial",
        derivative_use="noncommercial_only",
        provenance_quality="high",
        checked_at="2026-08-25",
        verdict="REJECTED",
        notes=(
            "Official multi-view product dataset (~147k products) — excellent structure, "
            "but NC license unsuitable for AiVai commercial product seed."
        ),
        download_strategy="aws_s3_selective",
        estimated_full_bytes=300_000_000_000,
        selective_download=True,
    ),
    SourceAudit(
        source_name="vikashrajluhaniwal_fashion_images_kaggle",
        official_url="https://www.kaggle.com/datasets/vikashrajluhaniwal/fashion-images",
        upstream_source=(
            "Kaggle e-commerce product images (~2900); Medium post references "
            "Fashion Product Images style data — upstream scrape rights unclear"
        ),
        dataset_license="not reliably readable (page errors / incomplete card)",
        image_content_license="unclear",
        commercial_use="unclear",
        redistribution="unclear",
        derivative_use="unclear",
        provenance_quality="low",
        checked_at="2026-08-25",
        verdict="REVIEW_REQUIRED",
        notes="Do not auto-download until license + provenance confirmed.",
        download_strategy="kaggle_full_archive",
        estimated_full_bytes=None,
        selective_download=False,
    ),
    SourceAudit(
        source_name="agrigorev_clothing_dataset_small",
        official_url="https://github.com/alexeygrigorev/clothing-dataset-small",
        upstream_source=(
            "Contributor-sourced clothing photos collected under CC0 intent "
            "(Tagias + volunteer forms); GitHub CC0-1.0"
        ),
        dataset_license="CC0-1.0 (Creative Commons Zero v1.0 Universal)",
        image_content_license="CC0-1.0 (publisher states commercial OK)",
        commercial_use="yes",
        redistribution="yes",
        derivative_use="yes",
        provenance_quality="high",
        checked_at="2026-08-25",
        verdict="APPROVED_FOR_BENCHMARK",
        notes=(
            "Preferred apparel/footwear seed source. Small subset (~10 classes). "
            "Maps to benchmark-only semantic labels (not production AiVai leaves)."
        ),
        download_strategy="github_raw_selective",
        estimated_full_bytes=50_000_000,
        selective_download=True,
    ),
]


def audits_by_verdict() -> dict[str, list[SourceAudit]]:
    out: dict[str, list[SourceAudit]] = {
        "APPROVED_FOR_BENCHMARK": [],
        "REVIEW_REQUIRED": [],
        "REJECTED": [],
    }
    for a in SOURCE_AUDITS:
        out.setdefault(a.verdict, []).append(a)
    return out


def get_audit(source_name: str) -> SourceAudit | None:
    for a in SOURCE_AUDITS:
        if a.source_name == source_name:
            return a
    return None
