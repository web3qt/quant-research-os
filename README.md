<h1 align="center">🧭 QROS</h1>

<p align="center"><b>量化研究治理操作系统</b></p>
<p align="center">把研究想法推进成 <b>可审查</b>、<b>可复现</b>、<b>可追溯</b> 的 research lineage。</p>

<p align="center">
  <img src="https://img.shields.io/badge/host-Codex%20%7C%20Claude%20Code-0F172A?style=flat-square" alt="hosts" />
  <img src="https://img.shields.io/badge/runtime-repo--local%20.qros-4C1D95?style=flat-square" alt="runtime" />
  <img src="https://img.shields.io/badge/workflow-contract--first-0F766E?style=flat-square" alt="workflow" />
  <img src="https://img.shields.io/badge/tests-1191%20pytest-9A3412?style=flat-square" alt="tests" />
</p>

<p align="center">
  <a href="#-quick-start">🚀 Quick Start</a> ·
  <a href="#-项目设计原理">🏗 Design</a> ·
  <a href="#-主流程">🪜 Pipeline</a> ·
  <a href="#-仓库地图">🗺 Repo Map</a> ·
  <a href="#-review-规则">🛡 Review</a> ·
  <a href="docs/README.md">Docs</a>
</p>

---

> [!IMPORTANT]
> **一句话定位**
> QROS 不替你发明 alpha，也不替某条研究线保存策略代码；它负责把研究过程里的 freeze、review、formal artifacts、failure routing 和 provenance 固定下来。

<br>

## ⚡ 为什么需要

Agent 已经能写代码、跑回测、生成报告。但量化研究的核心风险不在执行，在治理：

<p align="center">
<table>
<tr><td><b>阶段门禁</b></td><td>每个阶段的输入、输出、冻结和审查都有 formal contract，不能跳过</td></tr>
<tr><td><b>独立审查</b></td><td>写代码的 author 不能当自己的 reviewer，adversarial reviewer 必须独立</td></tr>
<tr><td><b>产物真值</b></td><td>空目录、placeholder 文件和合同说明文档不算阶段完成</td></tr>
<tr><td><b>失败处置</b></td><td>review 失败不是 debug，有专门的 failure routing、rollback 和 child lineage 路径</td></tr>
</table>
</p>

> [!NOTE]
> QROS 是 **框架仓**，不是策略实现仓。真实研究程序和正式研究产物应写在 active research repo 的 `outputs/<lineage_id>/` 下。

<br>

## 🏗 项目设计原理

QROS 的核心设计不是“多写几份报告”，而是把量化研究中最容易漂移的判断点，拆成可冻结、可复建、可审查的机器合同。

<p align="center">
<table>
<tr><td width="25%"><b>Contract-first</b></td><td>先定义 stage gate、freeze group、artifact expectation 和 review checklist，再让 agent 写代码或产物。合同在 `contracts/`，文档只负责解释。</td></tr>
<tr><td><b>Disk is truth</b></td><td>阶段状态以 active research repo 的 `outputs/<lineage_id>/` 磁盘产物为准，不以聊天记录、口头承诺或空目录为准。</td></tr>
<tr><td><b>Freeze before build</b></td><td>每个阶段先冻结本阶段会消费和产生的研究假设、数据范围、参数身份、执行边界，再物化 formal artifacts。</td></tr>
<tr><td><b>Review before advance</b></td><td>author lane 只能产出；review lane 独立检查 artifact、provenance、stage program 和 closure，PASS 前不能进入下一阶段。</td></tr>
<tr><td><b>Failure is a route</b></td><td>review 非正常放行不是继续普通推进，而是进入 failure handling，明确 retry、rollback、NO-GO 或 child lineage。</td></tr>
<tr><td><b>Lineage-local execution</b></td><td>真实阶段程序属于研究仓的 `outputs/<lineage_id>/program/`，每个可执行阶段必须有 `stage_program.yaml`、entrypoint、README 和 `program_execution_manifest.json`；QROS 只校验、调用和记账，不把共享 builder 当完成路径。</td></tr>
<tr><td><b>Host/runtime split</b></td><td>Codex / Claude Code 负责理解、对话和工具调度；QROS Python runtime 负责确定性状态机、合同校验、review / next-stage orchestration 和状态面板。</td></tr>
</table>
</p>

更细的运行机制看 [QROS 工作原理](docs/guides/how-qros-works.md)，文档入口看 [docs/README.md](docs/README.md)。

<br>

## 🚀 Quick Start

<table>
<tr>
<td width="50%">

### 🧩 安装

**Codex** — 在 Codex 里输入：

```text
Fetch and follow instructions from
https://raw.githubusercontent.com/
web3qt/quant-research-os/refs/heads/
main/.codex/INSTALL.md
```

重启 Codex，然后开始研究。

**Claude Code** — 直接告诉 Claude Code：

```text
请阅读并按照 https://raw.githubusercontent.com/
web3qt/quant-research-os/refs/heads/
main/.claude/INSTALL.md 的指示安装 QROS
```

</td>
<td width="50%">

### 🧪 5 分钟开始一条研究线

```text
$qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT，横截面研究

# 查看进度（只读）
$qros-progress

# 查看因子质量
$qros-factor-diagnostics 看下当前 lineage 的因子诊断
$qros-factor-diagnostics 看下 csf_test_evidence 阶段的 Rank IC、分层和稳定性
$qros-factor-diagnostics 看下 csf_backtest_ready 阶段的成本后收益和换手
$qros-factor-diagnostics 看下 csf_holdout_validation 阶段有没有样本外退化

# 查看信号质量
$qros-signal-diagnostics 看下当前 TSS lineage 的信号诊断
$qros-signal-diagnostics 看下 tss_backtest_ready 阶段的成本后收益、回撤和换手
$qros-signal-diagnostics 看下 tss_holdout_validation 阶段有没有样本外退化

# 更新版本
$qros-update
```

`qros-update` 是 Codex 和 Claude Code 的统一更新入口。用户只需要在 active research repo 根目录输入 `qros-update`；它会自动识别当前 host，刷新全局 QROS 安装，并重建当前 repo 的 `./.qros/` runtime。

默认路径会更新到最新稳定版本；如果你是框架开发者并且需要跟踪未发布主干，使用 `qros-update main`。

</td>
</tr>
</table>

<br>

## 📄 paper-to-spec data-spec-first

`$qros-paper-to-spec` 这个 Codex skill 名称保留，但旧 `strategy_spec` materializer 已移除，旧 baseline scaffold 已移除。

第一阶段采用 data-spec-first，产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_data_spec.yaml
```

第二阶段产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_signal_spec.yaml
```

第三阶段产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_train_freeze_spec.yaml
```

第四阶段产出：

```text
outputs/paper_to_spec/<paper_slug>/paper_test_evidence_spec.yaml
```

`paper_data_spec.yaml` 遵守 `contracts/paper_to_spec/paper_data_spec_contract.yaml`，可用 `runtime/scripts/validate_paper_data_spec.py` 做 deterministic validation。`paper_signal_spec.yaml` 遵守 `contracts/paper_to_spec/paper_signal_spec_contract.yaml`，可用 `runtime/scripts/validate_paper_signal_spec.py` 做 deterministic validation，用于记录 signal family、feature inputs、signal definition、lookahead controls、train/test policy、portfolio mapping、diagnostics 和 strict blocking 问题。`paper_train_freeze_spec.yaml` 遵守 `contracts/paper_to_spec/paper_train_freeze_spec_contract.yaml`，可用 `runtime/scripts/validate_paper_train_freeze_spec.py` 做 deterministic validation，用于冻结 train/test mode、parameters、train/test windows、split policy、selection policy、model training、refit policy、leakage controls 和 artifact identity。`paper_test_evidence_spec.yaml` 遵守 `contracts/paper_to_spec/paper_test_evidence_spec_contract.yaml`，可用 `runtime/scripts/validate_paper_test_evidence_spec.py` 做 deterministic validation，用于定义 frozen artifact binding、signal diagnostics、performance diagnostics、no-retune attestation、test result usage policy、provenance 和 evidence identity。当前不要把它当作 PDF 直接生成完整 strategy spec 或回测代码的入口。

完整说明见 [docs/guides/qros-paper-to-spec-usage.md](docs/guides/qros-paper-to-spec-usage.md)。

<br>

## 🪜 主流程

`qros-research-session` 是统一入口，推进到 route-specific `holdout_validation review` closure 和最终 next-stage confirmation 为止。

```text
mandate_admission -> mandate_freeze_confirmation_pending -> 01_mandate -> route selection
  ├─ time_series_signal
  │    -> 02_tss_data_ready
  │    -> 03_tss_signal_ready
  │    -> 04_tss_train_freeze
  │    -> 05_tss_test_evidence
  │    -> 06_tss_backtest_ready
  │    -> 07_tss_holdout_validation
  └─ cross_sectional_factor
       -> 02_csf_data_ready
       -> 03_csf_signal_ready
       -> 04_csf_train_freeze
       -> 05_csf_test_evidence
       -> 06_csf_backtest_ready
       -> 07_csf_holdout_validation
                                        -> review_complete
```

<br>

## 🗺 仓库地图

```
                    contracts/  ← machine-readable truth
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
      runtime/       skills/      templates/
   (bin/scripts/    (author/review   (SKILL.md
    tools/hooks)    failure/core)    generator)
           │             │
           ▼             ▼
     tests/          docs/
   (1191 tests)   (SOP/guides/visuals)
```

<p align="center">
<table>
<tr><td width="25%"><b>contracts/</b></td><td>机器真值层 — gate 定义、checklist、artifact schema</td></tr>
<tr><td><b>skills/</b></td><td>Agent 行为层 — 55 个 public skill bundles，覆盖 core、author、review、failure 和 diagnostics</td></tr>
<tr><td><b>runtime/</b></td><td>运行时层 — bin 入口 + scripts wrapper + tools 引擎</td></tr>
<tr><td><b>templates/</b></td><td>生成模板层 — host-agnostic review skill 模板</td></tr>
<tr><td><b>docs/</b></td><td>解释层 — 安装、SOP、使用指南</td></tr>
<tr><td><b>tests/</b></td><td>验证层 — 当前 `python -m pytest --collect-only -q` 收集 1191 条 pytest tests，覆盖全流程</td></tr>
</table>
</p>

<br>

## 🛡 Review 规则

<table>
<tr>
<td width="33%" align="center"><b>🧑‍⚖️ 独立审查</b></td>
<td width="33%" align="center"><b>📏 Formal Gate</b></td>
<td width="33%" align="center"><b>🚨 失败处置</b></td>
</tr>
<tr>
<td>每个 review 阶段要求<br>独立 adversarial reviewer<br>author 不能自审</td>
<td>reviewer 检查 artifact、<br>provenance 和 stage program<br>源码，不是走形式</td>
<td>FIX_REQUIRED 退回 author<br>NO-GO / CHILD LINEAGE<br>走 failure routing</td>
</tr>
</table>

<br>

## 🖥 支持的宿主

当前 README 校验环境：

| 宿主 | 当前版本 |
|------|------|
| Codex CLI | `codex-cli 0.134.0` |
| Claude Code | `2.1.152 (Claude Code)` |

<table>
<tr>
<td width="50%" align="center"><b>Codex</b></td>
<td width="50%" align="center"><b>Claude Code</b></td>
</tr>
<tr>
<td>

完整支持，当前主路径

```bash
# 安装
Fetch INSTALL.md

# review 子代理
spawn_agent (fork_context=false)

# skills 路径
~/.codex/skills/qros-*/
```

</td>
<td>

完整支持，通过 plugin

```bash
# 安装
/plugin install qros@quant-research-os

# review 子代理
.claude-plugin/agents/qros-reviewer.md

# skills 路径
.claude-plugin/skills/qros-*/
```

</td>
</tr>
</table>

<br>

## ✅ 质量体系

<table>
<tr>
<td width="33%" align="center"><b>🧪 测试</b></td>
<td width="33%" align="center"><b>🧭 Anti-Drift</b></td>
<td width="33%" align="center"><b>🔎 Verification</b></td>
</tr>
<tr>
<td>1191 条 pytest collected tests<br>bootstrap + contracts + runtime<br>session + review + skills<br>docs + anti_drift + pipeline</td>
<td>CI 自动回归检测<br>metamorphic testing<br>snapshot baseline<br>drift coverage matrix</td>
<td>smoke / full-smoke 分层<br>contract validation<br>semantic validation<br>upstream binding check</td>
</tr>
</table>

<br>

## 📚 常用文档

| 想了解 | 去哪里 |
|------|------|
| 🧭 文档导航 | [docs/README.md](docs/README.md) |
| 🛠 安装说明 | [docs/guides/installation.md](docs/guides/installation.md) |
| 🚀 Quick Start | [docs/guides/quickstart-codex.md](docs/guides/quickstart-codex.md) |
| 🧪 统一研究会话说明 | [docs/guides/qros-research-session-usage.md](docs/guides/qros-research-session-usage.md) |
| 🛡 Review 约束地图 | [docs/guides/qros-review-constraint-map.md](docs/guides/qros-review-constraint-map.md) |
| 📈 CSF 因子诊断 | [docs/guides/qros-factor-diagnostics.md](docs/guides/qros-factor-diagnostics.md) |
| 📉 TSS 信号诊断 | [docs/guides/qros-signal-diagnostics.md](docs/guides/qros-signal-diagnostics.md) |
| 🧷 阶段冻结字段说明 | [docs/guides/stage-freeze-group-field-guide.md](docs/guides/stage-freeze-group-field-guide.md) |
| 📝 Release Notes | [RELEASE_NOTES.md](RELEASE_NOTES.md) |

<br>

---

<p align="center">
  <sub>🧭 QROS · 治理框架 · 19 stage-program keys · 双宿主 · 1191 测试 · contract-first</sub>
</p>
