# QROS P0 Runtime Optimizations Design

## Goal

Reduce avoidable long-running QROS sessions by adding three runtime-backed capabilities:

- prebuild schema gates before full stage-program execution
- cached materialization digests for large review artifacts
- a stable review-cycle wrapper that prepares requests and handoff prompts

## Decisions

### 1. Stage Program Prebuild Gate

Stage programs may declare an optional `prebuild_schema_gate` in `stage_program.yaml`.

Runtime behavior:

- `invoke_stage_if_admitted()` validates the stage program as before.
- If `prebuild_schema_gate` is present, runtime runs the same entrypoint with configured `entrypoint_args` before full execution.
- The dry-run must write a JSON report to `report_path`.
- Runtime validates required columns, primary keys, coverage fields, and structured manifest fields from that report.
- If the dry-run fails, runtime raises `STAGE_PROGRAM_PREBUILD_FAILED` and does not run the full build.

This is deliberately a schema/contract gate, not a performance benchmark.

### 2. Review Digest Cache Ledger

`compute_author_materialization_digest()` should cache per-path digests in:

`review/state/materialization_digest_ledger.yaml`

The cache key uses path, size, mtime_ns, and file type. If unchanged, runtime reuses the existing digest instead of rereading 3G/7G artifacts. If changed, runtime recomputes and updates the ledger.

Directory digests still include child path metadata. This first version keeps correctness simple while avoiding repeated full-file reads for unchanged large files.

### 3. Review Cycle Prepare Wrapper

Add:

`./.qros/bin/qros-review-cycle prepare`

The wrapper should:

- resolve or accept `--stage-dir` / `--lineage-root`
- run the existing review-cycle preparation logic
- write request / handoff / receipt when reviewer ids are supplied
- emit JSON when `--json` is supplied
- print a reviewer handoff prompt and exact closer command for manual/Codex use

It should not call Codex `spawn_agent`; Python runtime cannot own that chat-level primitive.

## Non-goals

- No automatic spawned-agent execution in Python.
- No full replacement of stage-specific review skills.
- No rewrite of every existing lineage-local stage program.
- No forced dry-run requirement for all stages in v1; only programs that declare the gate are gated.

## Verification

Focused tests should cover:

- dry-run failure blocks full execution
- dry-run success permits full execution and writes provenance
- digest ledger reuses cached large-file digests when size/mtime are unchanged
- review-cycle prepare emits stable paths, prompt, and closer command
- repo-local install includes `qros-review-cycle`

Because this touches stage execution, review orchestration, and gate semantics, run focused tests, smoke, and full-smoke.
