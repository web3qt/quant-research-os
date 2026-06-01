# QROS Codex 使用指南

这份文档说明如何在 OpenAI Codex 中通过原生 skill discovery 使用 QROS。

## 快速安装

先在 active research repo 根目录打开 Codex，然后告诉 Codex：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

## 安装结果

安装说明会让 Codex 克隆或刷新 QROS 源码仓，把扁平化的 `qros-*` skills 安装到 `~/.codex/skills/`，初始化当前 active research repo 的 `./.qros/` runtime，并在当前仓库还没有 `AGENTS.md` 时写入轻量 research repo 操作合同。完成后重启 Codex，再在同一个 active research repo 中从 `qros-research-session` 开始。

## 工作方式

Codex 有原生 skill discovery。启动时它会扫描 `~/.codex/skills/`，解析 `SKILL.md` frontmatter，并按需加载匹配的 skill。

QROS 在克隆仓库的 `skills/` 下维护源码版 source bundles，`./setup` 会把它们扁平化安装到 Codex 的 `~/.codex/skills/` 目录。

安装后，QROS skills 会以扁平目录形式出现：

```text
~/.codex/skills/qros-research-session/
~/.codex/skills/qros-mandate-review/
...
```

## 使用方式

正常入口是 skill，而不是手动执行 runtime wrapper：

| 目的 | 在 Codex 里输入 |
| --- | --- |
| 开始或继续一条研究线 | `$qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT` |
| 查看 QROS 使用帮助 | `$qros-research-session help` |
| 查看当前研究进度 | `$qros-progress` |
| 查看横截面因子阶段质量诊断 | `$qros-factor-diagnostics` |
| 查看时序信号阶段质量诊断 | `$qros-signal-diagnostics` |
| paper-to-spec data-spec-first | `$qros-paper-to-spec` |
| 更新 QROS 到最新稳定版本，并刷新当前 repo 的 `./.qros/` | `$qros-update` |
| 高级/debug 手动进入某阶段 review | `$qros-mandate-review` |

### paper-to-spec data-spec-first

`$qros-paper-to-spec` 这个 Codex skill 名称保留，但旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。当前不要再把它当作 PDF 直接生成完整 strategy spec 或回测代码的入口。

第一版采用 data-spec-first，只产出 `outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml`。该产物遵守 `contracts/paper_to_spec/paper_data_spec_contract.yaml`，可用 `runtime/scripts/validate_paper_data_spec.py` 做 deterministic validation，重点记录 PDF 读取覆盖、crypto perpetual 数据需求、strict blocking 问题和 data implementation handoff。

完整说明见 `docs/guides/qros-paper-to-spec-usage.md`。

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

## Runtime 规则

QROS repo-local commands require Python 3.12。请从 active research repo 根目录运行 `qros-update`，让它通过 `uv` 创建或刷新 `./.qros/.venv`。不要为了绕过 Python 版本问题而跳过 `./.qros/bin/qros-*` wrapper、直接调用 `runtime/scripts/*`。

repo-local bootstrap 只在 active research repo 根目录缺少 `AGENTS.md` 时写入 QROS research repo 操作合同；已有 `AGENTS.md` 不会被覆盖。若你的项目已经有自己的 agent 规则，请把 QROS 边界手动合并进去：`outputs/<lineage_id>/` 和 `outputs/paper_to_spec/<paper_slug>/` 都属于 active research repo 的 repo-local 输出树，不属于 QROS framework repo；普通入口是 `$qros-research-session`，review 非正常放行必须转入 failure handling。

只有在需要 deterministic runtime 调试或手工恢复时，才使用项目本地 wrapper：

```bash
./.qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
./.qros/bin/qros-factor-diagnostics --stage csf_test_evidence
./.qros/bin/qros-signal-diagnostics --stage tss_test_evidence
./.qros/bin/qros-review-cycle prepare --host codex --reviewer-id reviewer-agent --reviewer-session-id reviewer-session --reviewer-agent-id reviewer-child-agent
./.qros/bin/qros-review
```

## 更新

在 Codex 里，推荐直接输入：

```text
qros-update
```

它默认会刷新最新稳定版本的安装副本，以及当前 repo 的 `./.qros/`。如果你是框架开发者并且要跟踪未发布主干，使用 `qros-update main`。

请从 active research repo 根目录运行。

如果你安装过旧版 QROS（例如还没有切到直接安装进 `~/.codex/skills` 的版本），请从 active research repo 根目录运行 `qros-update`，然后重启 Codex，确保旧的本地 skill 目录被替换。

## 卸载

```bash
rm -rf ~/.codex/skills/qros-*
```

如需彻底清理，也可以删除安装元数据、项目本地 runtime 和源码克隆：

```bash
rm -rf ~/.codex/qros
rm -rf ./.qros
rm -rf ~/workspace/quant-research-os
```

## 排查问题

### Skills 没有显示

1. 检查 Codex skills 是否已经安装：

```bash
ls ~/.codex/skills | grep qros-
```

2. 检查安装元数据和 runtime 目录是否存在：

```bash
test -f ~/.codex/qros/install-manifest.json
ls ./.qros/bin
```

3. 如果怀疑 repo-local runtime 和 QROS source repo 不一致，从 active research repo 运行 `<source_repo>/setup --host codex --mode repo-local --check`。如果输出包含 `source_repo_path drift`、`source_git_commit drift` 或 dirty-state drift，先确认当前 source checkout 是否正确，必要时 commit 或 stash 本地改动，再从 active research repo 根目录运行 `qros-update`。`qros-update` 默认会自动读取当前 repo 的 `.qros/install-manifest.json.host` 和当前 agent 环境；如需强制 Codex surface，可运行 `qros-update --host codex`。需要临时恢复时可以显式设置 `QROS_ALLOW_PROVENANCE_DRIFT=1`，但这只适合 emergency/manual recovery；需要锁定当前会话期望的治理仓时，用 `QROS_EXPECTED_SOURCE_REPO=/abs/path/to/quant-research-os`。

4. 重启 Codex。Skills 会在 Codex 启动时发现。
