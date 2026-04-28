# QROS for Codex

Guide for using QROS with OpenAI Codex via native skill discovery.

## Quick Install

Open Codex from the active research repo root first. Then tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

## Install Result

The fetched installer asks Codex to clone or refresh the QROS source repo, install the flat `qros-*` skills under `~/.codex/skills/`, and bootstrap the active research repo's `./.qros/` runtime. Restart Codex after that, then start with `qros-research-session` from the same active research repo.

## How It Works

Codex has native skill discovery. It scans `~/.codex/skills/` at startup, parses `SKILL.md` frontmatter, and loads matching skills on demand.

QROS keeps its authored source bundles in the cloned repo under `skills/`, then `./setup` flattens them into the installed Codex tree under `~/.codex/skills/`.

QROS skills become visible as flat installed directories:

```text
~/.codex/skills/qros-research-session/
~/.codex/skills/qros-mandate-review/
...
```

## Usage

Skills are the normal entrypoint:

| Intent | Command |
| --- | --- |
| 开始或继续一条研究线 | `$qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT` |
| 查看 QROS 使用帮助 | `$qros-research-session help` |
| 查看当前研究进度 | `$qros-progress` |
| 查看横截面因子阶段质量诊断 | `$qros-factor-diagnostics` |
| 查看时序信号阶段质量诊断 | `$qros-signal-diagnostics` |
| 更新 QROS 到远程最新版本，并刷新当前 repo 的 `./.qros/` | `$qros-update` |
| 手动进入某阶段 review | `$qros-mandate-review` |

因子 diagnostics 通常在 Codex 里直接问，例如：

```text
$qros-factor-diagnostics 看下当前 lineage 的因子诊断
$qros-factor-diagnostics 看下 csf_test_evidence 阶段的 Rank IC、分层和稳定性
$qros-factor-diagnostics 看下 csf_backtest_ready 阶段的成本后收益、回撤、换手和容量
$qros-factor-diagnostics 看下 csf_holdout_validation 阶段有没有退化或 regime shift
$qros-factor-diagnostics mean IC 为负说明什么，跟当前策略方向有没有冲突
$qros-factor-diagnostics 不要只给数字，用中文解释这些指标说明什么
```

时序信号 diagnostics 也应在 Codex 里直接问，例如：

```text
$qros-signal-diagnostics 看下当前 TSS lineage 的信号诊断
$qros-signal-diagnostics 看下 tss_test_evidence 阶段的 hit rate、forward return 和事件数量
$qros-signal-diagnostics 看下 tss_backtest_ready 阶段的成本后收益、回撤和换手
$qros-signal-diagnostics 看下 tss_holdout_validation 阶段有没有样本外退化
$qros-signal-diagnostics mean_rank_ic 小于 0 说明什么，按高信号做多会不会站错方向
$qros-signal-diagnostics 不要只给数字，用中文解释这些指标说明什么
```

If you need deterministic runtime debugging or manual recovery, use the project-local wrappers:

```bash
./.qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
./.qros/bin/qros-factor-diagnostics --stage csf_test_evidence
./.qros/bin/qros-signal-diagnostics --stage tss_test_evidence
./.qros/bin/qros-review-cycle prepare --reviewer-id reviewer-agent --reviewer-session-id reviewer-session --spawned-agent-id reviewer-child-agent
./.qros/bin/qros-review
```

## Updating

In Codex, the preferred path is:

```text
qros-update
```

It refreshes the published `main` install and the current repo's `./.qros/`.

Run it from the active research repo root.

If you installed an older QROS contract before the move to direct `~/.codex/skills` installs, run `qros-update` from the active research repo root and Restart Codex so stale local skill directories are replaced.

## Uninstalling

```bash
rm -rf ~/.codex/skills/qros-*
```

Optionally remove the install metadata, project-local runtime, and clone:

```bash
rm -rf ~/.codex/qros
rm -rf ./.qros
rm -rf ~/workspace/quant-research-os
```

## Troubleshooting

### Skills not showing up

1. Verify the installed Codex skills:

```bash
ls ~/.codex/skills | grep qros-
```

2. Check the install metadata and runtime tree exist:

```bash
test -f ~/.codex/qros/install-manifest.json
ls ./.qros/bin
```

3. If skill content looks stale, run `qros-update` from the active research repo root.

4. Restart Codex. Skills are discovered at startup.
