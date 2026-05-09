# 2026-05-06 Claude Code Support Design

## Status

Draft for review.

## Goal

让 QROS 支持用户把本项目安装到 Claude Code 中，同时不破坏当前 Codex-first 工作流、不降低 review isolation 和 stage gate 的治理强度。

这里的“支持 Claude Code”必须拆开理解：

- Claude Code 能发现 QROS 入口。
- Claude Code 能在 active research repo 初始化并使用 QROS repo-local runtime。
- Claude Code 能以与 Codex 等价的独立 reviewer 语义完成 review closure。

这三件事不能混成一个 plugin manifest。QROS 的核心产品不是一组提示词，而是 host agent 能力、QROS skills、active research repo 的 `./.qros` runtime、formal artifacts、review closure 和 failure routing 共同组成的治理系统。

## Current Project Facts

当前仓库事实如下：

- QROS 是流程、工具和治理规则仓，不是某条 live lineage 的策略实现仓。
- 当前用户主路径是 Codex-first：用户在 active research repo 打开 Codex，然后让 Codex fetch `.codex/INSTALL.md`。
- `runtime/tools/install_runtime.py` 当前只支持 `host = codex`。
- `user-global` 安装会把 flattened skills 写入 `~/.codex/skills/qros-*`。
- `repo-local` 安装会把当前 research repo 的 wrapper 写入 `./.qros/bin/*`，并写入 `./.qros/install-manifest.json`。
- QROS skills 不是独立 prompts。它们依赖 repo-local wrappers，例如 `./.qros/bin/qros-session`、`./.qros/bin/qros-review`、`./.qros/bin/qros-progress`。
- Review skills 当前硬编码 Codex tool semantics：`spawn_agent`、`send_input`、`fork_context: false`。
- Runtime 和 tests 当前也把 review 子代理 receipt、active review cycle、closer command 建模为 Codex-style spawned reviewer。
- Skill source tree 是 grouped nested layout，例如 `skills/core/qros-research-session/SKILL.md`，不是 `skills/qros-research-session/SKILL.md` 的 flat plugin layout。

因此，Claude Code plugin marketplace 只能解决 discovery 层，不能单独解决 repo-local runtime 和 review isolation。

## External Platform Facts

Claude Code plugin 系统支持：

- marketplace：通过 `/plugin marketplace add owner/repo` 添加 GitHub 仓中的 `.claude-plugin/marketplace.json`。
- plugin install：通过 `/plugin install plugin-name@marketplace-name` 安装。
- plugin components：可以提供 skills、commands、agents、hooks、MCP servers 等。
- plugin agents：可以放在 plugin 的 `agents/` 目录，安装后出现在 `/agents`，并可由 Claude 调用。
- subagents：Markdown + YAML frontmatter，独立 context，可限制工具权限。

References:

- <https://docs.claude.com/en/docs/claude-code/plugin-marketplaces>
- <https://code.claude.com/docs/en/plugins-reference>
- <https://docs.claude.com/en/docs/claude-code/subagents>
- <https://github.com/obra/superpowers>

## Design Principle

QROS 必须引入 host boundary：

```text
Host discovery layer
  -> Host bootstrap layer
  -> QROS repo-local runtime
  -> Host-neutral review protocol
  -> Deterministic QROS closer
```

规则：

- Plugin install 不等于 QROS workflow ready。
- `./.qros/bin` 是 active research repo 的执行边界，不能被 Claude plugin discovery 替代。
- Python runtime 不应依赖某个聊天宿主的工具名。
- Review closure 的事实来源仍然是 machine-readable review artifacts 和 deterministic closer，而不是 host chat transcript。
- Codex 当前路径必须保持不回退。

## Recommended Phasing

### Phase 1: `claude-plugin-preview`

目标：让 Claude Code 能安装并发现 QROS 入口，但明确标注为 preview。

Scope:

- 新增 `.claude-plugin/plugin.json`。
- 新增 `.claude-plugin/marketplace.json`。
- 在 plugin manifest 中显式声明 QROS nested skill paths，避免当前 grouped skill tree 被漏扫。
- 新增 Claude Code preview 安装文档。
- 新增 bootstrap / docs tests，锁定 plugin manifest、marketplace、skill path coverage 和 preview wording。

Non-goals:

- 不修改 stage flow。
- 不修改 review closure。
- 不修改 Codex install behavior。
- 不宣称 Claude Code 已完整支持 QROS review flow。
- 不把 docs 全面改成 host-neutral 口径。

User-facing wording:

```text
Claude Code support is preview. Plugin install makes QROS entries discoverable in Claude Code.
Full QROS workflow still requires bootstrapping the active research repo's ./.qros runtime.
Codex remains the fully supported host for review-subagent orchestration until host-neutral review is implemented.
```

Success criteria:

- Claude Code marketplace can see the QROS plugin.
- Plugin manifest includes QROS skills without flattening source tree manually.
- Docs do not imply full cross-host parity.
- Codex install tests remain unchanged and passing.

### Phase 2: `claude-repo-bootstrap`

目标：让 Claude Code 用户能在 active research repo 初始化和刷新 `./.qros` runtime。

Scope:

- 将 install host 从 hard-coded `codex` 扩展为 host profile：
  - `codex`
  - `claude-code`
- 拆出 host-specific global metadata roots：
  - Codex: `~/.codex/qros/install-manifest.json`
  - Claude Code: `~/.claude/qros/install-manifest.json`
- 为 Claude Code 提供 bootstrap command 或 skill，例如：
  - `/qros-bootstrap`
  - 或 `qros-bootstrap-current-repo`
- Claude bootstrap 在当前 active research repo 写入：
  - `./.qros/bin/*`
  - `./.qros/install-manifest.json`
- `qros-update` 改成 host-aware：
  - Codex: 刷新 `~/.codex/skills` 和当前 repo-local runtime。
  - Claude Code: 不直接修改 plugin-managed skill install，只刷新当前 repo-local runtime，并提示用 Claude plugin update 流程刷新 plugin。
- Docs 明确区分 discovery install 和 repo bootstrap。

Non-goals:

- 不要求 Claude plugin 自动在每个 research repo 写 `./.qros`。
- 不复制整套 runtime 源码到 plugin install 目录。
- 不改变 active research repo 是 lineage execution outputs 事实来源的边界。

Success criteria:

- 从 Claude Code 工作目录可以初始化 `./.qros/bin/qros-session`。
- `./.qros/bin/qros-progress`、`./.qros/bin/qros-session` 能继续以当前 research repo 为 cwd 写入或读取 `outputs/`。
- `install-manifest.json` 能记录 `host = claude-code`。
- Codex `user-global` / `repo-local` 测试继续通过。

### Phase 3: `host-neutral-review`

目标：让 review isolation 从 Codex-only tool semantics 升级为 host-neutral protocol。

Scope:

- 抽象 review launcher protocol：
  - `host`
  - `reviewer_invocation_kind`
  - `reviewer_identity`
  - `context_isolation_policy`
  - `handoff_delivery_method`
  - `allowed_read_scope`
  - `allowed_write_scope`
- Codex adapter:
  - `reviewer_invocation_kind = codex_spawn_agent`
  - `context_isolation_policy = fork_context_false`
  - 继续使用 `spawn_agent` / `send_input`
- Claude Code adapter:
  - `reviewer_invocation_kind = claude_plugin_agent`
  - `context_isolation_policy = separate_subagent_context`
  - 使用 plugin agent，例如 `qros-reviewer`
- 新增 `.claude-plugin/agents/qros-reviewer.md`，描述 adversarial reviewer 的职责、读写边界和禁止行为。
- 将 receipt 从 Codex-specific 语义迁移为 host-neutral 语义。可以保留旧文件名以降低迁移风险，但 payload 必须增加 host 和 invocation kind。
- `./.qros/bin/qros-review` 只验证 machine-readable receipt、request、raw findings、write-scope audit 和 closure，不依赖某个 host tool 名称。
- Review skills 文案改成 host-aware，不再全局硬编码 `spawn_agent`。

Non-goals:

- 不降低 reviewer independence。
- 不让 author 主会话自己写 canonical review result。
- 不接受没有 receipt 的 raw findings。
- 不以 Claude chat transcript 替代 review artifacts。

Success criteria:

- Codex review flow 继续通过现有 closure tests。
- Claude reviewer agent 只能写 `review/result/reviewer_findings.raw.yaml`。
- Deterministic closer 对 Codex 和 Claude Code 都验证同一套 review artifact contract。
- Docs 可以正式声明 Claude Code review flow supported。

## Alternatives Considered

### Alternative A: Only Add Claude Plugin Manifest

优点：

- 改动小。
- 可以快速让 Claude Code 发现 QROS skills。

缺点：

- 用户会误以为完整 workflow 已可用。
- 不会初始化 active research repo 的 `./.qros/bin`。
- Review skills 仍然引用 Codex-only `spawn_agent`。

Verdict: 只能作为 Phase 1 preview，不能作为完整方案。

### Alternative B: Fork A Separate Claude Skill Tree

优点：

- 可以快速写 Claude-specific wording。

缺点：

- 极易和 Codex skills 漂移。
- QROS stage semantics、artifact contract、review closure 文档会变成两套真值。
- 长期维护成本高。

Verdict: 不推荐。优先 host-aware generation 或 shared skills with host-specific sections。

### Alternative C: Jump Directly To Full Host-Neutral Review

优点：

- 一次性解决完整 Claude Code 支持。

缺点：

- 触及 review closure、receipt schema、generated review skills、runtime tests 和 docs。
- 风险最大，容易破坏当前 Codex 主路径。

Verdict: 不作为第一步。先完成 discovery + bootstrap，再做 review protocol。

## Testing Strategy

Phase 1 focused tests:

- `.claude-plugin/plugin.json` exists and is valid JSON.
- `.claude-plugin/marketplace.json` exists and points to this plugin.
- Plugin manifest references all QROS `SKILL.md` paths or an explicit supported subset.
- Docs mention Claude Code preview and do not claim full parity.
- Existing Codex install docs still mention `~/.codex/skills` and `Restart Codex`.

Phase 2 focused tests:

- `install_runtime.py` resolves `host = claude-code`.
- Claude repo-local install writes `./.qros/bin/*`.
- Claude manifest writes `host = claude-code`.
- Codex install behavior remains unchanged.
- Bootstrap command docs and tests lock the current research repo cwd behavior.

Phase 3 focused tests:

- Review receipt accepts host-neutral invocation metadata.
- Codex adapter still emits `fork_context: false`.
- Claude adapter emits `context_isolation_policy = separate_subagent_context`.
- Closer rejects missing receipt, wrong write scope, stale request, or author-modified review outputs.
- Generated / active review skills no longer hard-code Codex-only instructions outside Codex-specific sections.

Repository verification expectations:

- Phase 1 is docs / manifest / install-surface only: run focused tests plus docs/bootstrap minimal checks.
- Phase 2 touches install/runtime workflow: run focused tests, smoke, and likely full-smoke if session stage flow or gate semantics are affected.
- Phase 3 touches review orchestration: run focused tests, smoke, and full-smoke.

## Recommended Next Step

Implement Phase 1 and the design skeleton for Phase 2, but do not claim full Claude Code support until Phase 3 is complete.

First implementation slice:

1. Add tests for Claude plugin manifest and preview docs.
2. Add `.claude-plugin/plugin.json`.
3. Add `.claude-plugin/marketplace.json`.
4. Add Claude Code preview section to installation docs.
5. Run focused docs/bootstrap checks.

This gives users a safe installation discovery path while preserving QROS's current governance guarantees.
