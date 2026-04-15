# 🛠 Quant Research OS | 量化研究操作系统

QROS 是一个面向 agent 的阶段式研究治理框架。它不替你发明 alpha，也不替某条具体研究线代存真实业务代码。它做的事是把研究从“聊天里的想法”推进成一条**可审查、可复现、可追溯**的 research lineage，并用 freeze、review、formal artifacts、failure routing 和 lineage discipline 约束这条线如何被定义、推进、否决和重开。

如果你只想知道一句话版本：

- **这不是策略实现仓，这是研究流程框架仓。**
- **普通使用者的入口不是几十个 skill，而是一个：`qros-research-session`。**
- **真实研究产物不写在这个仓库里，而写在当前 active research repo 的 `outputs/<lineage_id>/` 下。**

## Codex 用户怎么开始

当前明确维护和文档化的宿主只有 `Codex`。

如果你本身就在 `Codex` 里工作，最短安装入口可以直接写成：

```text
Fetch and follow instructions from https://raw.githubusercontent.com/web3qt/quant-research-os/refs/heads/main/.codex/INSTALL.md
```

安装完成后，在 Codex 里直接开始：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-research-session help
```

真正进入某个 research repo 开工前，还要在该项目根执行一次：

```bash
~/workspace/quant-research-os/setup --host codex --mode repo-local
```

这一步会把 `./.qros/` 写进当前项目，而不是写进 home 目录。

## 当前主流程阶段图

```text
00_idea_intake -> 01_mandate
├─ time_series_signal
│  -> 02_data_ready
│  -> 03_signal_ready
│  -> 04_train_freeze
│  -> 05_test_evidence
│  -> 06_backtest_ready
│  -> 07_holdout_validation
└─ cross_sectional_factor
   -> 02_csf_data_ready
   -> 03_csf_signal_ready
   -> 04_csf_train_freeze
   -> 05_csf_test_evidence
   -> 06_csf_backtest_ready
   -> 07_csf_holdout_validation
```

QROS 负责固定阶段顺序、freeze/review gate、failure routing 和 lineage discipline。研究真正落地时，agent 必须在当前 research repo 中生成和维护正式产物。

当前 single-entry `qros-research-session` 的实际编排边界是：

- 一直推进到 `holdout_validation review`
- `holdout_validation review` 之后即停止

## 这项目是怎么设计的

### 1. 三层分离

QROS 是按三层设计的，理解这一点最重要。

1. **框架源仓**
   也就是你现在看到的这个 repo。这里放 workflow、skills、runtime、schema、SOP、测试。
2. **安装后的技能与运行时**
   安装后，Codex 从 `~/.codex/skills/qros-*` 发现技能；每个 research repo 再拥有自己的 `./.qros/` 本地 runtime。全局只保留 skills 和 install manifest，不再保留共享的 `~/.qros/` runtime 目录。
3. **真实研究仓**
   某条研究线真正的 formal artifacts、lineage-local stage program、review closure，都应写到当前 research repo 的 `outputs/<lineage_id>/` 下。

这三个层是故意分开的。框架仓负责制度，研究仓负责事实。

### 2. 五个核心设计层

#### Skill 层

`skills/` 里放的是 agent 该如何推进每个阶段的“行为合同”。

- `idea_intake / mandate / data_ready / ...`：author skill
- `failure_handling/`：失败分流与变更控制
- `core/qros-research-session`：统一 orchestrator

这些 skill 是**作者面和编排面**，不是研究事实本身。

#### Runtime 层

当前仓库已经把运行时实现收拢到 `runtime/`：

- `runtime/bin/`
- `runtime/scripts/`
- `runtime/tools/`
- `runtime/hooks/`

其中：

- `runtime/bin/` 是稳定入口
- `runtime/scripts/` 是命令行 wrapper
- `runtime/tools/` 是 deterministic runtime 本体
- `runtime/hooks/` 是运行期辅助

关键入口包括：

- `runtime/tools/research_session.py`
- `runtime/tools/*_runtime.py`
- `runtime/tools/lineage_program_runtime.py`
- `runtime/scripts/run_research_session.py`
- `runtime/scripts/run_verification_tier.py`

这一层负责：

- 检测当前阶段
- scaffold draft
- 校验 freeze group 是否完成
- 校验 lineage-local stage program 是否存在
- 校验 formal outputs / provenance / review closure

它不负责替你“脑补研究结论”。

#### Contract 层

`contracts/stages/workflow_stage_gates.yaml` 是 machine-readable gate truth。  
`docs/sop/main-flow/research_workflow_sop.md` 和各阶段 `*_sop_cn.md` 是解释层。  
`docs/guides/stage-freeze-group-field-guide.md` 是 grouped freeze 字段说明层。

冲突时以 `contracts/stages/workflow_stage_gates.yaml` 为准。

#### Verification 层

`tests/` 和验证脚本保证这个流程不是“靠 README 维持秩序”。

日常至少有两层：

- `smoke`
- `full-smoke`

例如：

```bash
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

如果需要 deterministic 调试或手工验证，也可以用：

```bash
./.qros/bin/qros-verify --tier smoke
```

#### Instruction / Harness 层

`harness/` 不是业务示例目录，也不是给普通使用者上手主流程用的 demo。

它的职责是服务根 `AGENTS.md`，用于：

- 演示分层 `AGENTS.md` 地图应该如何组织
- 验证从不同子目录启动 Codex 时，哪些 instruction files 会被实际读取
- 给文档、skills、tools、tests 这几类目录提供 instruction 近场化写法样例

所以 `harness/` 更接近一个 **instruction-system support subtree**，而不是一个“功能例子”。

### 2.5 当前顶层

- `contracts/`：代码直接读取的真值层
- `skills/`：agent 行为层
- `runtime/bin/ + runtime/scripts/ + runtime/tools/ + runtime/hooks/`：运行时实现层
- `templates/`：生成模板层
- `docs/`：解释层
- `tests/`：验证层
- `harness/`：服务根 `AGENTS.md` 的 instruction support 层

目录分层现在已经和这套语义对齐，不再只是“语义上先分层”的过渡态。

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

- `docs/guides/stage-freeze-group-field-guide.md`

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
- `runtime/bin/`：稳定用户入口
- `runtime/scripts/`：命令行 wrapper
- `runtime/tools/`：runtime 本体、gate 校验、program/provenance 处理
- `runtime/hooks/`：运行期辅助
- `contracts/`：machine-readable contract truth，供 runtime、review engine 和 skill 生成直接读取
- `docs/sop/main-flow/`：阶段解释和操作规范
- `docs/guides/`：安装、上手、字段说明、使用路径
- `docs/visuals/`：面向教学和展示的图稿
- `templates/`：技能或 review 生成模板
- `tests/`：bootstrap、安装、技能、runtime、anti-drift、stage flow 回归测试
- `harness/`：服务根 `AGENTS.md` 的 instruction / orchestration 支撑子树，用于分层 AGENTS 演示与验证

## 谁需要懂到什么程度

### 普通使用者 / 研究员

不需要先读懂所有 skill。先会这几件事就够了：

- 安装
- 从 `qros-research-session` 开始
- 知道 agent 会在 grouped freeze 上停下来问
- 知道正式产物要写进当前 research repo

### 维护者 / 扩展技能的人

这时才需要系统理解 `skills/`、`runtime/tools/`、`contracts/`、`tests/` 之间的关系。

## 快速开始

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

进入某个新的 research repo 后，再在该项目根执行：

```bash
~/workspace/quant-research-os/setup --host codex --mode repo-local
```

## 用户如何真正开始使用

安装完成后，实际入口很简单：

1. 在 QROS 框架仓执行 `./setup --host codex --mode user-global`
2. 重启 Codex
3. 在当前 research repo 根执行 `~/workspace/quant-research-os/setup --host codex --mode repo-local`
4. 在新会话里直接输入 `qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT`
5. 如果想先看说明，就输入 `qros-research-session help`

如果你想直接验证安装是否正常，也可以运行：

```bash
./.qros/bin/qros-verify --tier smoke
```

## 日常使用

正常使用时，直接在 Codex 里通过 skill 名称进入：

```text
qros-research-session 帮我研究这个想法：BTC 领动高流动性 ALT
qros-research-session help
```

如果要做手动诊断、恢复或直接验证 runtime 行为，再调用稳定 wrapper：

```bash
./.qros/bin/qros-session --raw-idea "BTC leads high-liquidity alts after shock events"
./.qros/bin/qros-review
```

如果你想看更细的实际运行行为、状态字段、stage gate 语义和恢复方式，可以继续读：

- `docs/guides/qros-research-session-usage.md`
- `docs/guides/qros-verification-tiers.md`
- `docs/sop/main-flow/research_workflow_sop.md`

## 当前关键制度变化

- 所有 `*_review` 阶段都要求**独立的 adversarial reviewer**
- reviewer 必须检查 stage artifact、provenance，以及 lineage-local `program/<stage>/` 源码
- 只有 `CLOSURE_READY_*` 结果才能继续运行 `./.qros/bin/qros-review` 写 closure artifacts
- `FIX_REQUIRED` 会把流程退回 author-fix loop，禁止直接写 `stage_completion_certificate.yaml`
- review 闭环之上还有 **governance-candidate lane**：post-rollout review findings 会写成 `governance_signal.json`，再聚合到 `governance/review_findings_ledger.jsonl` 与 `governance/candidates/*.yaml`
- 候选优先级固定为：`hard_gate -> template_constraint -> regression_test`
- human governance decision 也不会直接激活 policy；真正生效仍要走正常 repo 变更

## 运行时布局

**Codex 安装：**

```text
~/.codex/skills/qros-*
~/.codex/qros/install-manifest.json
<research-repo>/.qros/
```

Codex 扫描 `~/.codex/skills/`。`./setup --mode user-global` 会把扁平 `qros-*` skills 直接写进去，并记录安装来源；`repo-local` 只会把当前项目需要的 `./.qros/bin/*` 和本地 install manifest 写进 research repo。

## 安装后更新

**Codex：**

```bash
git pull && ./setup --host codex --mode user-global
```

然后在需要继续使用的 research repo 根，再执行：

```bash
~/workspace/quant-research-os/setup --host codex --mode repo-local
```

如果你之前装的是旧版，例如还在用 `~/.agents/skills`，也按上面两步重新执行一次，然后**重启 Codex**，让本地安装树刷新到当前合同。

## 延伸阅读

- [文档导航](docs/README.md)
- [QROS 工作原理：两层运行时架构](docs/guides/how-qros-works.md) — 宿主 AI Runtime 与 QROS Python Runtime 如何协作
- [Codex 安装说明](docs/guides/installation.md)
- [QROS for Codex](docs/README.codex.md)
- [Codex 快速开始](docs/guides/quickstart-codex.md)
- [QROS 统一研究会话说明](docs/guides/qros-research-session-usage.md)
- [阶段冻结字段说明](docs/guides/stage-freeze-group-field-guide.md)

## 常见问题

- Codex 看不到技能：确认 `~/.codex/skills/` 里存在 `qros-*`
- 感觉安装内容过旧：执行 `git pull && ./setup --host codex --mode user-global`，再在当前 research repo 根执行 `~/workspace/quant-research-os/setup --host codex --mode repo-local`，然后重启 Codex
- 不确定安装是否正常：新开会话，输入 “帮我研究一个量化策略” 测试自动触发
