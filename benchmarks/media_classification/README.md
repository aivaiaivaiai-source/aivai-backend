# AiVai Media Classification — Offline Benchmark Harness (Substage 3B-1)

**MODE:** Benchmark tooling only. Not production inference.

## Purpose

Run the **same frozen listing-centric dataset** through interchangeable classifier
adapters and produce comparable, reproducible reports.

No production request path imports this package.

## Privacy — READ BEFORE ADDING DATA

- **Do not commit** real user listing photos.
- Dataset images live in a **local/ignored** directory (see `.gitignore`).
- Do not include phones, addresses, or other PII in manifests/notes.
- Prefer EXIF-stripped images.
- External API benchmarks require separate legal/policy approval.
- Use only approved/legal image sources.

## Layout

```
benchmarks/media_classification/
  README.md
  manifest.schema.json
  example_manifest.jsonl
  adapters/          # ClassifierAdapter implementations
  runner/            # validate / run / compare
  metrics/           # quality + performance aggregation
  catalog/           # example + public-seed catalog snapshots
  seed/              # 3B-2 provenance gate + seed builder
  fixtures/          # tiny synthetic assets for smoke tests
  data/              # downloaded seed images (gitignored)
  reports/           # generated run outputs (mostly gitignored)
```

## Quick start (synthetic smoke)

From `aivai_backend` root:

```bash
python -m benchmarks.media_classification validate \
  --manifest benchmarks/media_classification/example_manifest.jsonl \
  --catalog benchmarks/media_classification/catalog/example_catalog.json \
  --images-root benchmarks/media_classification/fixtures

python -m benchmarks.media_classification run \
  --manifest benchmarks/media_classification/example_manifest.jsonl \
  --catalog benchmarks/media_classification/catalog/example_catalog.json \
  --images-root benchmarks/media_classification/fixtures \
  --adapter dummy \
  --image-max-edge 640 \
  --image-count-mode first_3

python -m benchmarks.media_classification compare \
  reports/<run_a> reports/<run_b>
```

## Public seed builder (Substage 3B-2)

Legal/provenance-gated seed for offline benchmark. **Does not** touch production.

```bash
python -m benchmarks.media_classification inspect-sources
python -m benchmarks.media_classification build-seed --dry-run
python -m benchmarks.media_classification build-seed --seed 42 --target-cases 120
python -m benchmarks.media_classification validate-seed
python -m benchmarks.media_classification summarize-seed
```

Downloaded images land only under `data/` (gitignored). Only
`APPROVED_FOR_BENCHMARK` sources are downloaded automatically.

## Dry run (adapters)

```bash
python -m benchmarks.media_classification run ... --dry-run
```

Validates config/manifest/catalog/adapter availability; does **not** call classify.

## Adapters (3B-1)

| Adapter | Purpose |
|---------|---------|
| `dummy` | Deterministic wiring tests |
| `oracle` | **ORACLE_TEST_ONLY** — returns ground truth for metrics self-check |

Real models (SigLIP2, EVA, VLM, external) come in later substages.

## Catalog snapshot

Benchmark uses a frozen `category_catalog.json`, not live DB.
Optional future utility may export a snapshot from a **dev** DB — never mutate production catalog.
