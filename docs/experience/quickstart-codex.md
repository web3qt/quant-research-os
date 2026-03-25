# QROS Quickstart For Codex

## 1. Install

Choose one:

```bash
./setup --host codex --mode user-global
```

or

```bash
./setup --host codex --mode repo-local
```

## 2. Start A Lineage

```bash
python scripts/scaffold_idea_intake.py --lineage-root outputs/<lineage_id>
```

This creates `outputs/<lineage_id>/00_idea_intake/`.

## 3. Author The Intake

Use:

- `qros-idea-intake-author`

Fill the intake artifacts and make sure `idea_gate_decision.yaml` reaches `GO_TO_MANDATE`.

## 4. Build The Mandate

```bash
python scripts/build_mandate_from_intake.py --lineage-root outputs/<lineage_id>
```

Use:

- `qros-mandate-author`

This creates `outputs/<lineage_id>/01_mandate/`.

## 5. Run Mandate Review

Move into the relevant stage directory or provide the right context, then run:

```bash
python scripts/run_stage_review.py
```

Use:

- `qros-mandate-review`

## 6. What You Should See

After review, QROS writes closure artifacts such as:

- `latest_review_pack.yaml`
- `stage_gate_review.yaml`
- `stage_completion_certificate.yaml`

## Next

After `mandate` passes review, continue into `data_ready` and the later stage review flow.
