# Host-Neutral Review Protocol Design

## Goal

将 review infrastructure 从 Codex 专有的 `spawn_agent`/`fork_context`/`send_input` 语义抽象为 host-neutral protocol，使 Codex 和 Claude Code 都能执行完整的 adversarial review workflow。

## Architecture

```
Review Launcher Protocol (host, invocation_kind, isolation_policy, handoff_method)
  ├── Codex Adapter: spawn_agent + fork_context:false + send_input
  └── Claude Code Adapter: .claude-plugin/agents/ + separate_subagent_context
                │
        Host-Neutral Review Runtime
        request → receipt → handoff → findings → result → closure → audit
```

## Receipt Schema Migration

Backward compatibility: none. Hard cutover. Runtime only reads new format.

```
OLD filename: spawned_reviewer_receipt.yaml
NEW filename: reviewer_receipt.yaml

OLD filename: spawned_reviewer_handoff_manifest.yaml
NEW filename: reviewer_handoff_manifest.yaml
```

Field mapping:

| Old Field | New Field | Codex Value | Claude Code Value |
|-----------|-----------|-------------|-------------------|
| fork_context | context_isolation_policy | fork_context_false | separate_subagent_context |
| spawned_agent_id | reviewer_agent_id | (unchanged semantics) | (unchanged semantics) |
| spawn_mode | execution_mode | spawned_agent / review_session | (same values) |
| (none) | host | codex | claude-code |
| (none) | reviewer_invocation_kind | codex_spawn_agent | claude_plugin_agent |
| (none) | handoff_delivery_method | send_input | agent_task_context |

Full receipt payload:

```yaml
review_cycle_id: "..."
host: "codex"  # or "claude-code"
launcher_owner: "qros-runtime-launcher"
launcher_session_id: "..."
launcher_thread_id: "..."
execution_mode: "spawned_agent"  # or "review_session"
reviewer_invocation_kind: "codex_spawn_agent"  # or "claude_plugin_agent"
context_isolation_policy: "fork_context_false"  # or "separate_subagent_context"
handoff_delivery_method: "send_input"  # or "agent_task_context"
reviewer_agent_id: "..."
write_root: "review/result"
handoff_manifest_path: "review/request/reviewer_handoff_manifest.yaml"
handoff_manifest_digest: "..."
requested_reviewer_identity: "..."
requested_reviewer_session_id: "..."
receipt_written_at: "..."
```

## Skill Template

Template `templates/skills/review-stage/SKILL.md.tmpl` uses host variables:

| Template Variable | Codex | Claude Code |
|-------------------|-------|-------------|
| `{{HOST_LABEL}}` | Codex | Claude Code |
| `{{HOST_SPAWN_TOOL}}` | `spawn_agent` | 通过 `.claude-plugin/agents/qros-reviewer.md` 创建 task |
| `{{HOST_ISOLATION_POLICY}}` | `fork_context` 必须是 `false` | subagent 独立上下文（由 Claude Code 平台保证） |
| `{{HOST_HANDOFF_METHOD}}` | `send_input` | 将 handoff manifest 作为 task prompt 传入 |
| `{{HOST_SPAWNED_AGENT_ID_FLAG}}` | `--spawned-agent-id` | `--reviewer-agent-id` |

## Skill Generation

`gen_codex_stage_review_skills.py` → renamed to `gen_stage_review_skills.py`, added `--host` parameter.

Generated skills output:
- `--host codex` → `skills/{stage}/qros-{stage}-review/SKILL.md` (18 stages, existing paths)
- `--host claude-code` → `.claude-plugin/skills/{stage}/qros-{stage}-review/SKILL.md` (18 stages, new paths)

## Claude Code Reviewer Agent

New file: `.claude-plugin/agents/qros-reviewer.md`

Defines a subagent with:
- Read scope: `review/request/*`, `author/formal/*`
- Write scope: `review/result/reviewer_findings.raw.yaml` only
- Must not modify `author/formal/*`
- Must not run `qros-review`
- Receives handoff context via task prompt (not `send_input`)

Agent definition is dynamically augmented with stage-specific gate before each review, written to `.claude-plugin/agents/qros-reviewer-{stage}.md`.

## Bin Wrapper Changes

- `qros-spawn-reviewer` → **removed**, use `qros-review-cycle prepare`
- `qros-start-spawned-review` → **removed**, use `qros-review-cycle prepare`
- `qros-review-cycle prepare` gains `--host codex|claude-code` flag
- `qros-review-cycle prepare` `--spawned-agent-id` → renamed to `--reviewer-agent-id`

## Host Detection

`qros-review-cycle prepare` resolves host via:
1. `--host` CLI argument (explicit override)
2. Fallback: read `./.qros/install-manifest.json` → `host` field

## Files Changed

| File | Action |
|------|--------|
| `runtime/tools/review_skillgen/adversarial_review_contract.py` | Receipt schema migration, constant renames |
| `runtime/tools/review_skillgen/review_session_runtime.py` | `start_spawned_review_cycle()` → `start_review_cycle(host=)`, handoff prompt host-aware |
| `runtime/scripts/review_cycle.py` | Add `--host`, rename `--spawned-agent-id` → `--reviewer-agent-id` |
| `runtime/tools/review_skillgen/protocol_validator.py` | Update constant references |
| `runtime/tools/review_skillgen/review_engine.py` | Update `_runtime_identity_from_receipt()` |
| `templates/skills/review-stage/SKILL.md.tmpl` | Host variables |
| `runtime/tools/review_skillgen/render.py` | Accept host vars, pass to template |
| `runtime/scripts/gen_codex_stage_review_skills.py` | Rename, add `--host` |
| `.claude-plugin/agents/qros-reviewer.md` | **New** |
| `runtime/bin/qros-spawn-reviewer` | **Removed** |
| `runtime/bin/qros-start-spawned-review` | **Removed** |
| 18 generated SKILL.md under `skills/` | Regenerated with new template |
| 18 generated SKILL.md under `.claude-plugin/skills/` | **New** (Claude Code variants) |
| `tests/review/` | Updated for new schema, new tests for host-neutral receipt |

## Non-Goals

- `qros-review` (closer) — operates on file artifacts, host-independent
- `qros-audit-reviewer` — same
- `qros-review-preflight` — same
- Review checklist / gate schema YAMLs — data layer, host-independent
- Backward compatibility with old receipt format — hard cutover, agent handles migration

## Implementation Order

1. Receipt schema migration (contract + constants)
2. Template update + render.py
3. review_session_runtime.py (host-aware handoff/closer)
4. protocol_validator.py + review_engine.py (new constant refs)
5. review_cycle.py script (--host, rename flags)
6. gen_stage_review_skills.py (rename, --host)
7. Regenerate all 18+18 review SKILL.md
8. .claude-plugin/agents/qros-reviewer.md
9. Remove qros-spawn-reviewer, qros-start-spawned-review
10. Tests update + new tests
