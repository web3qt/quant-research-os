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
| 开始或继续一条研究线 | `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT` |
| 查看 QROS 使用帮助 | `qros-research-session help` |
| 查看当前研究进度 | `qros-progress` |
| 查看横截面因子阶段质量诊断 | `qros-factor-diagnostics` |
| 更新 QROS 到远程最新版本，并刷新当前 repo 的 `./.qros/` | `qros-update` |
| 手动进入某阶段 review | `qros-mandate-review` |

If you need deterministic runtime debugging or manual recovery, use the project-local wrappers:

```bash
./.qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
./.qros/bin/qros-factor-diagnostics --stage csf_test_evidence
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
