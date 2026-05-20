# QROS Update Stable Tag Design

## Purpose

`qros-update` currently defaults to tracking `main`.

This is the wrong default for ordinary users running updates from Codex or Claude Code. The normal update path should resolve to the latest stable published version, while developers should still be able to explicitly opt into `main` or pin an exact tag/commit for debugging and recovery.

This design changes `qros-update` into a target-driven updater with a simple user-facing model:

- `qros-update` -> latest stable tag
- `qros-update main` -> latest `origin/main`
- `qros-update <tag>` -> exact tag
- `qros-update <sha>` -> exact commit ref

## Scope

In scope:

- `runtime/tools/update_runtime.py`
- `runtime/scripts/run_qros_update.py`
- repo-local/global updater wrappers if they need CLI alignment
- install/update manifests written by QROS install/update flows
- tests for update target resolution and managed source repo update behavior
- install/update docs

Out of scope:

- introducing a new external release service
- signed releases or channel manifests
- changing the ordinary install entrypoint
- changing repo-local runtime bootstrap semantics beyond update-source selection

## User Model

Ordinary user UX should be:

```text
qros-update
```

Meaning: update to the latest stable published version.

Developer UX should be:

```text
qros-update main
```

Meaning: update to the latest `origin/main`.

Advanced/debug UX should remain available:

```text
qros-update v0.4.12
qros-update abc1234
```

Meaning: pin to an exact tag or exact commit ref.

The public docs should only *prominently* teach:

- `qros-update`
- `qros-update main`

Tag/SHA forms remain supported but are documented as advanced or recovery usage.

## Internal Update Modes

Internally, the updater should resolve one of four target modes:

- `stable`
- `main`
- `tag`
- `ref`

The external CLI does not need to expose the word “channel” to ordinary users. That vocabulary is internal.

## CLI Parsing Model

The new preferred CLI shape is:

```text
qros-update [target]
```

Parsing rules:

1. No positional target
   - resolve to `stable`
2. Target is `main`
   - resolve to `main`
3. Target matches a known semver tag
   - resolve to `tag`
4. Target looks like a commit SHA
   - resolve to `ref`
5. Otherwise
   - fail with a clear user-facing error

Legacy compatibility:

- existing `--branch main` remains supported for a compatibility period
- if both positional target and legacy `--branch` are provided, positional target wins

## Update Target Model

Introduce a single resolved update target model in runtime, for example:

```python
@dataclass(frozen=True)
class UpdateTarget:
    mode: Literal["stable", "main", "tag", "ref"]
    requested_ref: str | None
    resolved_git_ref: str
    resolved_git_tag: str | None
```

Examples:

### `qros-update`

```python
UpdateTarget(
    mode="stable",
    requested_ref=None,
    resolved_git_ref="refs/tags/v0.4.12",
    resolved_git_tag="v0.4.12",
)
```

### `qros-update main`

```python
UpdateTarget(
    mode="main",
    requested_ref="main",
    resolved_git_ref="origin/main",
    resolved_git_tag=None,
)
```

### `qros-update v0.4.12`

```python
UpdateTarget(
    mode="tag",
    requested_ref="v0.4.12",
    resolved_git_ref="refs/tags/v0.4.12",
    resolved_git_tag="v0.4.12",
)
```

### `qros-update abc1234`

```python
UpdateTarget(
    mode="ref",
    requested_ref="abc1234",
    resolved_git_ref="abc1234",
    resolved_git_tag=None,
)
```

## Stable Tag Resolution

Stable resolution should not use lexical tag ordering.

Rules:

1. fetch tags from origin
2. select only semver-style tags
3. ignore prerelease tags by default (`-rc`, `-beta`, etc.)
4. sort by semantic version, not string order
5. choose the highest stable version

Examples:

- `v0.10.0` > `v0.9.9`
- `v0.4.12` > `v0.4.11`
- `v0.4.12-rc1` should not beat `v0.4.11` in default stable mode

If no stable tag exists, updater should fail with a clear error rather than silently falling back to `main`.

## Managed Source Repo Update Behavior

The existing updater is branch-first. It should become target-first.

### Stable / Tag

Expected flow:

1. `git fetch --tags origin`
2. `git fetch origin`
3. clean managed worktree
4. checkout the resolved tag in detached HEAD mode

Do **not** run `git pull origin <tag>`.

### Main

Expected flow:

1. `git fetch origin main`
2. clean managed worktree
3. checkout `main`
4. `git pull --ff-only origin main`

### Ref / SHA

Expected flow:

1. `git fetch origin`
2. clean managed worktree
3. checkout the resolved SHA in detached HEAD mode

If the requested ref cannot be resolved, fail clearly.

## Recovery Behavior

Recovery behavior should follow target mode.

### Stable / Tag

- refetch tags
- clean worktree
- re-checkout detached tag

### Main

- keep existing branch-based recovery behavior
- reset to `origin/main` when needed

### Ref / SHA

- refetch origin
- clean worktree
- re-checkout requested SHA

Recovery must not silently switch from `stable` or `tag` mode back to `main`.

## Manifest Changes

Keep existing provenance fields:

- `source_repo_path`
- `source_git_commit`
- `source_git_dirty`

Add new update-source fields:

- `update_channel`
- `requested_ref`
- `resolved_ref_type`
- `resolved_git_ref`
- `resolved_git_tag`

Recommended manifest examples:

### Stable

```json
{
  "update_channel": "stable",
  "requested_ref": null,
  "resolved_ref_type": "tag",
  "resolved_git_ref": "refs/tags/v0.4.12",
  "resolved_git_tag": "v0.4.12",
  "source_git_commit": "abc123..."
}
```

### Main

```json
{
  "update_channel": "main",
  "requested_ref": "main",
  "resolved_ref_type": "branch",
  "resolved_git_ref": "origin/main",
  "resolved_git_tag": null,
  "source_git_commit": "def456..."
}
```

### Exact Tag

```json
{
  "update_channel": "tag",
  "requested_ref": "v0.4.12",
  "resolved_ref_type": "tag",
  "resolved_git_ref": "refs/tags/v0.4.12",
  "resolved_git_tag": "v0.4.12",
  "source_git_commit": "abc123..."
}
```

### Exact SHA

```json
{
  "update_channel": "ref",
  "requested_ref": "abc1234",
  "resolved_ref_type": "commit",
  "resolved_git_ref": "abc1234",
  "resolved_git_tag": null,
  "source_git_commit": "abc1234..."
}
```

## Manifest Compatibility

Older manifests do not contain the new update-source fields.

Compatibility rules:

- old manifests remain readable
- absence of new fields is not an error
- the first successful run of the new updater should backfill the new fields
- provenance and drift checks should continue to function when new fields are missing

This is a manifest extension, not a manifest format reset.

## Legacy Wrapper Compatibility

Old wrappers may still call:

```text
run_qros_update.py --branch main
```

Compatibility policy:

- keep parsing legacy `--branch`
- map `--branch main` to the same internal target as positional `main`
- do not require every already-installed wrapper to be updated before the new updater works

The user-facing docs should move to the new positional-target model even while the compatibility parser remains.

## Documentation Changes

Update all user-facing install/update docs from “latest published main” to “latest stable version/tag”.

Required doc changes:

- `.codex/INSTALL.md`
- `.claude/INSTALL.md`
- `docs/guides/installation.md`
- `docs/README.codex.md`
- `docs/guides/quickstart-codex.md`
- any other live docs that currently describe `qros-update` as following `main`

Recommended wording:

- `qros-update` updates to the latest stable published version
- `qros-update main` tracks the latest mainline code for development and debugging

Advanced forms (`qros-update <tag>`, `qros-update <sha>`) should be documented as advanced or recovery usage.

## Testing Strategy

Minimum test coverage should include:

### CLI / parsing

- no positional target -> `stable`
- positional `main` -> `main`
- positional semver tag -> `tag`
- positional SHA-like ref -> `ref`
- positional target overrides legacy `--branch`

### Stable resolution

- semver sorting is correct
- prerelease tags are excluded from default stable mode
- missing stable tags fail clearly

### Managed repo update behavior

- stable/tag modes use detached tag checkout, not branch pull
- main mode still uses branch update flow
- ref mode uses detached commit checkout

### Manifest

- new fields are written correctly
- old manifests remain readable
- update backfills the new fields

### Documentation

- docs mention `qros-update`
- docs describe `qros-update` as stable by default
- docs describe `qros-update main` as the developer path

## Non-Goals

- no GitHub Release API integration in this phase
- no signed release verification
- no beta/canary channel in this phase
- no release-manifest infrastructure in this phase

## Success Criteria

- `qros-update` defaults to the latest stable tag
- `qros-update main` updates to latest main
- explicit tag and SHA forms remain supported
- updater no longer treats every update target as a branch
- manifests record update-source semantics, not just commit SHA
- old wrappers and old manifests continue to work
- docs no longer teach “latest main” as the ordinary user update path
