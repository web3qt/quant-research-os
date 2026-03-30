# QROS data_ready Labeled Classification Dataset

## Purpose
Labeled dataset for evaluating and optimizing data_ready failure classification accuracy.
Used in the Feedback Descent loop to iteratively improve SKILL.md rules.

## Schema
Each sample has:
- `input.yaml`: Research context + data spec attempt
- `output.yaml`: Ground truth classification (7 classes)

## Classes (7)
1. `DATA_MISSING` — Data source or field missing, cannot satisfy minimum research contract
2. `DATA_MISALIGNMENT` — Time alignment, sampling frequency, session boundary incorrect
3. `LEAKAGE_FAIL` — Future function, label leakage, out-of-sample info in research window
4. `QUALITY_FAIL` — Missing/stale/outlier thresholds exceeded
5. `SCHEMA_FAIL` — Field name, type, unit, semantic mismatch with contract
6. `REPRO_FAIL` — Cannot reproduce same table under same version config
7. `SCOPE_FAIL` — Data preparation deviates from mandate-declared research scope

## Distribution (30 samples)
| Class | Train | Test | Total |
|-------|-------|------|-------|
| DATA_MISSING | 3 | 1 | 4 |
| DATA_MISALIGNMENT | 4 | 1 | 5 |
| LEAKAGE_FAIL | 5 | 1 | 6 |
| QUALITY_FAIL | 3 | 1 | 4 |
| SCHEMA_FAIL | 3 | 1 | 4 |
| REPRO_FAIL | 3 | 1 | 4 |
| SCOPE_FAIL | 2 | 1 | 3 |
| **Total** | **23** | **7** | **30** |

## Evaluation
```bash
# Run classification evaluation
python scripts/evaluate_classification.py --split train
python scripts/evaluate_classification.py --split test
```
