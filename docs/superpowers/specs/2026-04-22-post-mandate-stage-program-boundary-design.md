# Post-Mandate Stage Program Boundary Design

## Goal

把 `mandate` 之后所有 stage 的 authoring 边界收紧成一条明确规则：

- 真实研究流里，阶段产物必须由当前 lineage 的真实 stage program 生成。
- 这个 stage program 由 Codex agent 在 author lane 中显式编写或刷新。
- 公共 runtime 不再后台静默生成 thin wrapper 并把它当成合法的 lineage-local program。

本设计同时覆盖 `time_series_signal` 与 `cross_sectional_factor` 两条主线。

## Problem Statement

历史实战暴露出一个边界不清的问题：当前系统虽然在文档上强调 `mandate` 之后需要 `lineage-local stage program`，但公共 runtime 仍保留了自动补 program 的路径，部分 stage runtime 也仍可生成 demo/placeholder 风格的 formal outputs。这样会制造一个危险灰区：

- 看起来已有 `program/<route>/<stage>/run_stage.py`
- 看起来 formal artifacts 也“存在”
- 但实际上只是 framework 默认 builder、thin wrapper 或 fake artifact 在工作

这会让研究员和 reviewer 在 author lane、preflight、review lane 之间反复消耗，而不是尽早把问题挡在正确的边界上。

## Confirmed Product Decisions

以下边界已明确冻结：

1. `mandate` 之后，真实研究流里不接受 thin wrapper 作为合法 stage program。
2. `mandate` 之后，真实研究流里不接受 placeholder/demo/contract-only fake artifact。
3. 真实 stage program 的作者不是研究员本人，而是 Codex agent。
4. Codex agent 的职责不是补壳，而是编写“这一步产物如何生成”的真实程序。
5. `run_stage.py` 与关键 helper 必须带清晰、简短、面向维护者的中文注释。
6. 以上约束要写进 post-mandate author skills，而不是只停留在运行时实现细节中。

## Definitions

### Lineage-Local Stage Program

当前 lineage 在某个 stage 下的正式程序目录，例如：

- `outputs/<lineage_id>/program/mandate/`
- `outputs/<lineage_id>/program/time_series/data_ready/`
- `outputs/<lineage_id>/program/cross_sectional_factor/test_evidence/`

它至少包含：

- `stage_program.yaml`
- `README.md`
- `run_stage.py`

但“存在这三个文件”只是最低结构条件，不等于 research-usable。

### Thin Wrapper

名义上位于当前 lineage 的 `run_stage.py`，但本质只是在无条件转调 framework 默认 builder，没有体现这条研究线自己的：

- 上游 formal inputs
- 数据来源与路径
- 关键计算逻辑
- 产物生成过程

在真实研究流里，这类程序视为无效。

### Fake Artifact

以下对象都视为 fake artifact：

- placeholder 文本伪装的 `parquet/csv/json`
- demo universe / toy panel / toy metric
- 只有合同语义、没有真实 machine output 的 markdown
- contract-only stub

这些对象可以存在于 fixture/demo-only 环境，但不允许出现在真实研究流 author/review 路径。

## Architecture

### 1. Session / Runtime Boundary

`qros-session` / `run_research_session.py` 在 `mandate` 之后的职责收敛为：

- 检测当前 stage 与 gate 状态
- 检查当前 lineage 是否已有合法 stage program
- 调用合法 stage program
- 检查 formal outputs 与 provenance 是否已经 materialize

它不再承担下面的职责：

- 后台自动生成 stage program
- 静默补 thin wrapper
- 用 framework-side shared builder 冒充当前 lineage 的 author build

缺 program 时，runtime 仍可复用 `STAGE_PROGRAM_MISSING` 这类 machine code，但 `next_action` / `resume_hint` 必须明确表达：

- 当前 stage 需要由 Codex author skill 显式生成 lineage-local stage program
- program 必须解释本阶段 formal artifacts 如何生成

### 2. Author Skill Boundary

`mandate` 之后的每个 author skill 都要把“生成/刷新本 stage program”变成标准职责。

标准 author 顺序应为：

1. 读取 freeze draft 与上游 formal artifacts
2. 明确本 stage formal outputs contract
3. 显式编写或刷新本 lineage 的 stage program
4. 用该 program 真实生成 formal artifacts
5. 检查 artifacts 与 provenance
6. 才允许进入 review-ready

这里生成的 program 必须体现：

- 用了哪些上游 artifacts
- 用了哪些数据文件/路径
- 核心计算如何进行
- 生成了哪些 formal outputs

关键步骤必须写中文注释，尤其是：

- 数据读取/筛选
- 合同字段映射
- 关键计算步骤
- gate 相关分支
- 易误解的 provenance/manifest 绑定逻辑

### 3. Program Identity Gate

当前 stage program 的合法性需要拆成两层：

- contract valid：manifest 结构、entrypoint、输入输出路径等合法
- identity valid：它是这条 lineage 的真实 authoring program，而不是 thin wrapper

`mandate` 之后两个 gate 都必须通过。

判 invalid 的典型场景包括：

- `run_stage.py` 只是无条件调用 framework builder
- 关键 helper 与 entrypoint 没有真实计算语义
- 缺少必要中文注释，导致无法解释产物如何生成

### 4. Preflight / Review Boundary

review lane 不应该再承担“第一轮发现 author 没有真的写程序/没有真的生成产物”的职责。

因此 `qros-review-preflight` 需要前移并收紧，至少承担两类 hard gate：

- program identity gate
- artifact realism gate

只有在 preflight 通过后，当前 stage 才进入 reviewer lane。

reviewer 的重点则回到：

- 审当前 lineage 的真实 stage program
- 审 formal outputs 与 source logic 是否一致
- 审 adversarial findings / metric gate / closure verdict

## Testing Strategy

测试要明确分成两套语义。

### 1. Real Research Flow Tests

这些测试锁定真实研究流的边界：

- `mandate` 之后缺 program 时停在 `STAGE_PROGRAM_MISSING`
- auto-generated thin wrapper 不能推进 author build
- fake artifact 不能进入 review-ready
- preflight 必须在 reviewer lane 前挡住 program identity / artifact realism 问题

### 2. Fixture / Demo / Test Support Tests

保留测试辅助生成 program 的能力，但要明确其语义为：

- fixture-only helper
- 不是公共 runtime 的真实研究流路径

这类 helper 只能由测试代码显式调用，不能再通过 `run_research_session` 主路径隐式触发。

### 3. Skill / Doc Contract Tests

需要新增或加强存在性/契约测试，锁定：

- post-mandate author skills 明确承担 stage program authoring
- 中文注释要求被写入 skill 约束
- `program_hash` 明确是整个 `program_dir` 的 hash
- 文档明确禁止 thin wrapper / fake artifact 进入真实研究流

## Documentation Changes

需要同步修改以下解释层对象：

- `docs/guides/qros-research-session-usage.md`
- `docs/sop/main-flow/research_workflow_sop.md`
- `docs/guides/qros-review-shared-protocol.md`
- `docs/guides/qros-verification-tiers.md`
- 所有 `mandate` 之后的 author skills

文档口径必须统一成：

- Codex 显式生成真实 lineage-local stage program
- runtime 不再后台自动补 program
- 真实研究流禁 thin wrapper / fake artifact
- fixture/demo-only 路径必须与真实研究流隔离
- `program_hash` 基于整个 `program_dir`
- `run_stage.py` 与关键 helper 必须中文注释

## Migration Strategy

迁移重点不是“删掉 helper”，而是把旧语义安全搬离生产主路径。

### 1. Production Path

从 `research_session` 主路径移除 post-mandate auto-program generation 行为。

### 2. Test Support Path

`materialize_stage_program()` 这类 helper 保留为测试支持能力，但不再代表真实研究流 author build。

更理想的状态是：

- helper 被迁到更明显的 test-support / fixture 语义位置
- 测试若需要 fixture program，必须显式调用它

### 3. Anti-Drift / Replay Fixtures

anti-drift、snapshot、fixture replay 仍然可以保留 fake objects，但必须：

- 物理隔离在 fixture 体系里
- 语义上标明为 fixture-only
- 不走真实 author/review 主路径

## Rollout Order

建议按下面顺序落地，降低回归风险：

1. 先写 failing tests，锁定新边界
2. 再改 `research_session` / runtime 主路径，切断 post-mandate auto-program generation
3. 再改 program validation / preflight，加入 program identity 与 artifact realism gate
4. 再改 post-mandate author skills，把显式 stage program authoring 与中文注释要求写成强约束
5. 再迁移 test helpers / fixture helpers，和真实研究流主路径解耦
6. 最后统一 docs / SOP / protocol

## Verification Requirements

这次变更触及：

- `qros-research-session` stage flow / gate semantics
- route split / authoring seam
- review / display / next-stage orchestration
- stage-program authoring contract

因此最低验证要求不是只跑 focused tests，而是：

- focused tests
- `smoke`
- `full-smoke`

对应命令：

```bash
python -m pytest <focused tests>
python runtime/scripts/run_verification_tier.py --tier smoke
python runtime/scripts/run_verification_tier.py --tier full-smoke
```

## Non-Goals

本次设计不包含以下重构：

- 引入 bootstrap/demo mode 与 research mode 的双模式产品重构
- 重写所有 stage runtime 的具体算法实现
- 改造每个研究阶段的 formal metric 定义
- 改写 anti-drift fixture 语义之外的历史快照内容

## Open Implementation Questions

实现阶段仍需明确的工程问题包括：

1. post-mandate 的“thin wrapper”识别规则采用静态 AST 判定、manifest 白名单规则，还是混合策略
2. 中文注释要求由 skill 契约测试锁定，还是同时加 preflight/source inspection gate
3. `STAGE_PROGRAM_MISSING` 是否继续复用，还是新增更细的 authoring-required code
4. `materialize_stage_program()` 是迁到 test helper 命名空间，还是保留原位置但彻底退出生产主路径
