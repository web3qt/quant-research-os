# 🛠 Quant Research OS | 量化研究操作系统

[English](README_EN.md) | 中文

QROS 是一个面向 agent 的阶段式研究治理框架。它不替你发明 alpha，也不替某条具体研究线代存真实业务代码。它做的事是把研究从“聊天里的想法”推进成一条**可审查、可复现、可追溯**的 research lineage，并用 freeze、review、formal artifacts、failure routing 和 lineage discipline 约束这条线如何被定义、推进、否决和重开。

如果你只想知道一句话版本：

- **这不是策略实现仓，这是研究流程框架仓。**
- **普通使用者的入口不是几十个 skill，而是一个：`qros-research-session`。**
- **真实研究产物不写在这个仓库里，而写在当前 active research repo 的 `outputs/<lineage_id>/` 下。**

## 当前主流程阶段图

```text
00_idea_intake -> 00_mandate
├─ time_series_signal
│  -> 01_data_ready
│  -> 02_signal_ready
│  -> 03_train_freeze
│  -> 04_test_evidence
│  -> 05_backtest_ready
│  -> 06_holdout_validation
└─ cross_sectional_factor
   -> 01_csf_data_ready
   -> 02_csf_signal_ready
   -> 03_csf_train_freeze
   -> 04_csf_test_evidence
   -> 05_csf_backtest_ready
   -> 06_csf_holdout_validation
```

QROS 负责固定阶段顺序、freeze/review gate、failure routing 和 lineage discipline。研究真正落地时，agent 必须在当前 research repo 中生成和维护正式产物。

## 这项目是怎么设计的

### 1. 三层分离

QROS 是按三层设计的，理解这一点最重要。

1. **框架源仓**
   也就是你现在看到的这个 repo。这里放 workflow、skills、runtime、schema、SOP、测试。
2. **安装后的技能与运行时**
   安装后，Codex 从 `~/.codex/skills/qros-*` 发现技能，从 `~/.qros/` 使用稳定 wrapper 和 runtime 资产。
3. **真实研究仓**
   某条研究线真正的 formal artifacts、lineage-local stage program、review closure，都应写到当前 research repo 的 `outputs/<lineage_id>/` 下。

这三个层是故意分开的。框架仓负责制度，研究仓负责事实。

### 2. 四个核心设计层

#### Skill 层

`skills/` 里放的是 agent 该如何推进每个阶段的“行为合同”。

- `idea_intake / mandate / data_ready / ...`：author skill
- `failure_handling/`：失败分流与变更控制
- `core/qros-research-session`：统一 orchestrator

这些 skill 是**作者面和编排面**，不是研究事实本身。

#### Runtime 层

`tools/` 和 `scripts/` 里放的是 deterministic runtime。

关键入口包括：

- `tools/research_session.py`
- `tools/*_runtime.py`
- `tools/lineage_program_runtime.py`
- `scripts/run_research_session.py`
- `scripts/run_verification_tier.py`

这一层负责：

- 检测当前阶段
- scaffold draft
- 校验 freeze group 是否完成
- 校验 lineage-local stage program 是否存在
- 校验 formal outputs / provenance / review closure

它不负责替你“脑补研究结论”。

#### Contract 层

`contracts/stages/workflow_stage_gates.yaml` 是 machine-readable gate truth。  
`docs/main-flow-sop/research_workflow_sop.md` 和各阶段 `*_sop_cn.md` 是解释层。  
`docs/experience/stage-freeze-group-field-guide.md` 是 grouped freeze 字段说明层。

冲突时以 `contracts/stages/workflow_stage_gates.yaml` 为准。

#### Verification 层

`tests/` 和验证脚本保证这个流程不是“靠 README 维持秩序”。

日常至少有两层：

- `smoke`
- `full-smoke`

例如：

```bash
python scripts/run_verification_tier.py --tier smoke
python scripts/run_verification_tier.py --tier full-smoke
```

如果已经按安装文档落好稳定 wrapper，也可以用：

```bash
~/.qros/bin/qros-verify --tier smoke
```

### 3. 单入口，而不是全技能直用

对大多数用户，QROS 的设计不是“背所有 SKILL 名称”。  
推荐始终从统一入口开始：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-research-session help
```

这个入口会：

- 创建或恢复 lineage
- 判断当前真实阶段
- 推导当前该由哪个 skill 接手
- 在需要治理确认时停下来交互
- 在可以确定性落盘时写出 formal artifacts
- 在 review 失败时切到 failure handling，而不是继续硬推阶段

如果你第一次看到 `research_intent`、`scope_contract`、`window_contract`、`delivery_contract` 这类 group 名，先看：

- `docs/experience/stage-freeze-group-field-guide.md`

### 4. 从 mandate 开始的硬门

从 lineage-local stage program hard gate 起，每个可执行阶段都必须在当前 research repo 的 `outputs/<lineage_id>/program/` 下保留 route-aware stage program，至少包含：

- `stage_program.yaml`
- `README.md`
- 被 manifest 引用的 entrypoint

同时，对应阶段产物目录必须写出：

- `program_execution_manifest.json`

QROS runtime 只负责：

- gate 校验
- 合同校验
- stage program 调用
- 产物验证
- provenance 记账

它不再把 framework-side shared builder 当作完成来源。

## Repo 边界

这个仓库是 **研究流程框架仓**，不是某条具体策略线的真实研究产物仓。

- 这里提供：workflow、skills、runtime、gate discipline、review discipline、schema、SOP、verification
- 这里不承载：某条具体研究线的真实业务实现、因子研究代码、回测实现本体
- 实际研究应在当前 research repo 的 `outputs/<lineage_id>/` 下推进

空目录、placeholder 文件、只有合同语义的说明文档，都不能被当作阶段完成。

## 仓库目录怎么读

你不需要一次看完所有内容，但最好知道每个目录在干什么：

- `skills/`：author / failure / orchestrator 技能源文件
- `tools/`：阶段 runtime、lineage program gate、install runtime、verification
- `scripts/`：稳定 CLI wrapper 和确定性入口
- `contracts/`：machine-readable contract truth，供 runtime、review engine 和 skill 生成直接读取
- `docs/main-flow-sop/`：阶段解释和操作规范
- `docs/experience/`：安装、上手、字段说明、使用路径
- `docs/show/`：面向教学和展示的图稿
- `templates/`：技能或 review 生成模板
- `tests/`：bootstrap、安装、技能、runtime、anti-drift、stage flow 回归测试

## 谁需要懂到什么程度

### 普通使用者 / 研究员

不需要先读懂所有 skill。先会这几件事就够了：

- 安装
- 从 `qros-research-session` 开始
- 知道 agent 会在 grouped freeze 上停下来问
- 知道正式产物要写进当前 research repo

### 组内带教 / 熟练使用者

建议再理解：

- 每个 major stage 的 freeze groups 在问什么
- review 阶段为什么会卡住
- failure handling 什么时候介入

### 维护者 / 扩展技能的人

这时才需要系统理解 `skills/`、`tools/`、`contracts/`、`tests/` 之间的关系。

## 快速开始

### Claude Code

```text
/plugin marketplace add web3qt/quant-research-os
/plugin install quant-research-os@qros
```

安装后在新会话中提及量化研究想法，QROS 会自动激活。

### Codex

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

或者手动安装：

```bash
git clone https://github.com/web3qt/quant-research-os.git ~/workspace/quant-research-os
cd ~/workspace/quant-research-os
./setup --host codex --mode user-global
```

然后 **Restart Codex**。

## 用户如何真正开始使用

安装完成后，按这 4 步走即可：

1. 运行：

```bash
./setup --host codex --mode user-global
```

2. 重启 Codex
3. 在新会话里直接输入：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
```

4. 如果想先看说明：

```text
qros-research-session help
```

如果你想直接验证安装是否正常，也可以运行：

```bash
~/.qros/bin/qros-verify --tier smoke
```

## 日常使用

正常使用时，直接在研究仓里通过 skill 名称进入：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-mandate-review
```

如果要做手动诊断或恢复，可以直接调用稳定 wrapper：

```bash
~/.qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
~/.qros/bin/qros-review
```

如果你想看更细的实际运行行为、状态字段、stage gate 语义和恢复方式，可以继续读：

- `docs/experience/qros-research-session-usage.md`
- `docs/experience/qros-verification-tiers.md`
- `docs/main-flow-sop/research_workflow_sop.md`

## 当前关键制度变化

- 所有 `*_review` 阶段都要求**独立的 adversarial reviewer**
- reviewer 必须检查 stage artifact、provenance，以及 lineage-local `program/<stage>/` 源码
- 只有 `CLOSURE_READY_*` 结果才能继续运行 `~/.qros/bin/qros-review` 写 closure artifacts
- `FIX_REQUIRED` 会把流程退回 author-fix loop，禁止直接写 `stage_completion_certificate.yaml`
- review 闭环之上还有 **governance-candidate lane**：post-rollout review findings 会写成 `governance_signal.json`，再聚合到 `governance/review_findings_ledger.jsonl` 与 `governance/candidates/*.yaml`
- 候选优先级固定为：`hard_gate -> template_constraint -> regression_test`
- human governance decision 也不会直接激活 policy；真正生效仍要走正常 repo 变更

## 运行时布局

**插件安装（Claude Code）:**

插件系统自动管理 skill 发现和 hook 注入。

**手动安装（Codex / 通用）:**

```text
~/.codex/skills/qros-*
~/.qros/
```

Codex 扫描 `~/.codex/skills/`。`./setup --mode user-global` 会把扁平 `qros-*` skills 直接写进去。

## 安装后更新

**Claude Code:**

```text
/plugin update quant-research-os
```

**手动安装:**

```bash
git pull && ./setup --host codex --mode user-global
```

如果你之前装的是旧版，例如还在用 `~/.agents/skills`，或还保留 display 相关旧 skill/runtime，也按上面这条重新执行一次，然后**重启 Codex**，让本地安装树刷新到当前合同。

## 延伸阅读

- [文档导航](docs/README.md)
- [Claude Code 安装说明](.claude/INSTALL.md)
- [Codex 安装说明](docs/experience/installation.md)
- [QROS for Codex](docs/README.codex.md)
- [Codex 快速开始](docs/experience/quickstart-codex.md)
- [QROS 统一研究会话说明](docs/experience/qros-research-session-usage.md)
- [阶段冻结字段说明](docs/experience/stage-freeze-group-field-guide.md)

## 常见问题

- Claude Code 看不到技能：确认已执行 `/plugin install web3qt/quant-research-os`，重启会话
- Codex 看不到技能：确认 `~/.codex/skills/` 里存在 `qros-*`
- 感觉安装内容过旧：Claude Code 执行 `/plugin update quant-research-os`；手动安装执行 `git pull && ./setup --host codex --mode user-global`，然后重启 Codex
- 不确定安装是否正常：新开会话，输入 “帮我研究一个量化策略” 测试自动触发
