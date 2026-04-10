# Stage Author Review Layout Design

## Goal

把每个 stage 目录从“所有产物都堆在一起”的平面结构，改成对 author 过程件、author 正式产物、review 请求、review 结果、review closure、review governance 明确分层的目录合同。

## Problem

当前 `outputs/<lineage>/<stage>/` 同时承载：

- author 冻结草案
- author 正式产物
- review request
- review result
- review closure
- governance signal

这会带来三个直接问题：

1. 阶段目录语义不清，author 和 review 的边界混在一起。
2. downstream stage 难以明确“到底该消费哪一层产物”。
3. review closure 文件和正式产物混放，人的认知负担和脚本的路径判断都容易失真。

## Approved Directory Contract

每个阶段统一改成下面这套结构：

```text
outputs/<lineage>/<stage>/
  author/
    draft/
      <freeze draft / transition approval / author 过程件>
    formal/
      <正式 stage artifacts>
  review/
    request/
      adversarial_review_request.yaml
    result/
      adversarial_review_result.yaml
    closure/
      latest_review_pack.yaml
      stage_gate_review.yaml
      stage_completion_certificate.yaml
    governance/
      governance_signal.json
```

## Semantics

### 1. `author/draft/`

只放 author 阶段过程件，不是正式 stage outputs。

典型文件：

- `*_freeze_draft.yaml`
- `*_transition_approval.yaml`
- 分组确认过程中的中间产物

约束：

- downstream stage 不允许消费 `draft/`
- review checklist 不把 `draft/` 当 formal outputs

### 2. `author/formal/`

只放阶段正式产物。

典型文件：

- stage contract 文档
- parquet / json / csv / markdown 正式输出
- `artifact_catalog.md`
- `field_dictionary.md`
- formal gate decision 文档

约束：

- downstream stage 只允许从这里取输入
- `artifact_catalog.md` 和 `field_dictionary.md` 归这里，因为它们描述的是正式交付物

### 3. `review/request/`

只放 reviewer 输入合同。

当前第一版固定包含：

- `adversarial_review_request.yaml`

### 4. `review/result/`

只放 reviewer 原始结果。

当前第一版固定包含：

- `adversarial_review_result.yaml`

### 5. `review/closure/`

只放 closure 产物。

固定包含：

- `latest_review_pack.yaml`
- `stage_gate_review.yaml`
- `stage_completion_certificate.yaml`

阶段完成判定规则：

- stage 是否 review complete，只看 `review/closure/stage_completion_certificate.yaml`

### 6. `review/governance/`

只放从本次 review 派生出的治理信号。

当前第一版固定包含：

- `governance_signal.json`

## Hard Rules

这是一次目录合同重构，不保留旧路径兼容。

硬规则如下：

1. 所有 stage runtime 只能把正式产物写到 `author/formal/`
2. 所有 author draft / approval 文件只能写到 `author/draft/`
3. 所有 review request/result/closure/governance 文件必须写到对应 `review/*/`
4. `stage_completion_certificate.yaml` 不再允许写在 stage 根目录
5. downstream stage 只能读上游 `author/formal/`
6. review engine 和 closure writer 不再向 stage 根目录写文件
7. 上下文推断必须把 `stage_root`、`author_formal_dir`、`review_closure_dir` 明确区分

## Stage Detection Changes

当前很多状态判断依赖：

```text
outputs/<lineage>/<stage>/stage_completion_certificate.yaml
```

新规则改成：

```text
outputs/<lineage>/<stage>/review/closure/stage_completion_certificate.yaml
```

同理：

- `adversarial_review_request.yaml` 改到 `review/request/`
- `adversarial_review_result.yaml` 改到 `review/result/`
- `latest_review_pack.yaml` / `stage_gate_review.yaml` 改到 `review/closure/`
- `governance_signal.json` 改到 `review/governance/`

## Runtime Impact

需要改三类 runtime：

### 1. Author runtime

例如：

- `tools/mandate_runtime.py`
- `tools/data_ready_runtime.py`
- `tools/signal_ready_runtime.py`
- `tools/csf_signal_ready_runtime.py`
- `tools/csf_train_runtime.py`
- `tools/test_evidence_runtime.py`
- `tools/backtest_runtime.py`
- `tools/holdout_runtime.py`
- `tools/csf_holdout_runtime.py`

这些 runtime 需要：

- 统一创建 `author/draft/` 和 `author/formal/`
- 原来落在 stage 根目录的正式产物迁到 `author/formal/`
- 原来落在 stage 根目录的 draft / approval 迁到 `author/draft/`

### 2. Review runtime

例如：

- `tools/review_skillgen/closure_writer.py`
- `tools/review_governance_runtime.py`
- `tools/review_skillgen/context_inference.py`
- `tools/review_skillgen/review_engine.py`

这些 runtime 需要：

- request / result / closure / governance 分开写
- review context 推断能从 `stage_root` 或 `review/*` 进入
- closure existence 检查改到 `review/closure/`

### 3. Session / Orchestration runtime

例如：

- `tools/research_session.py`
- `scripts/run_research_session.py`
- `scripts/run_stage_review.py`

这些 runtime 需要：

- 所有上游完成判定改读 `review/closure/stage_completion_certificate.yaml`
- 所有上游正式输入改读 `author/formal/`
- session 提示里明确 author / review 子目录

## Test Impact

这是一次广泛但机械性的路径合同变更。

必改测试类型：

1. stage runtime tests
2. stage review engine tests
3. research session stage detection tests
4. anti-drift scenario fixtures
5. review writer / governance runtime tests
6. docs / path 示例相关测试

重点风险：

- fixture 里大量硬编码 `stage_dir / "stage_completion_certificate.yaml"`
- fixture 里大量硬编码 `stage_dir / "artifact_catalog.md"`
- review engine 默认在 stage 根目录找 request / result

## Documentation Impact

需要同步更新：

- `docs/main-flow-sop/research_workflow_sop.md`
- `docs/review-sop/stage_completion_standard_cn.md`
- `docs/review-sop/stage_completion_certificate_template_cn.md`
- `docs/experience/codex-stage-review-skill-usage.md`
- `docs/experience/closure-artifact-writer-usage.md`
- `docs/experience/qros-research-session-usage.md`
- `docs/gates/workflow_stage_gates.yaml`

原则：

- 所有路径示例都要明确 `author/formal/` 与 `review/closure/`
- 不再用 stage 根目录假装同时代表 author 和 review

## Example

`00_mandate` 目标结构：

```text
outputs/topic_a/00_mandate/
  author/
    draft/
      mandate_freeze_draft.yaml
      mandate_transition_approval.yaml
    formal/
      mandate.md
      research_scope.md
      time_split.json
      parameter_grid.yaml
      run_config.toml
      artifact_catalog.md
      field_dictionary.md
  review/
    request/
      adversarial_review_request.yaml
    result/
      adversarial_review_result.yaml
    closure/
      latest_review_pack.yaml
      stage_gate_review.yaml
      stage_completion_certificate.yaml
    governance/
      governance_signal.json
```

## Rejected Alternatives

### A. 只给 review 文件加前缀

拒绝原因：

- 没解决 stage 根目录混杂问题
- 仍然没有把 author / review 边界做成路径合同

### B. 把 author / review 提到 lineage 根层级

拒绝原因：

- 会破坏现有 `stage_root` 概念
- 改动面过大，不适合当前仓库演进节奏

### C. 继续往下细分 `author/formal/machine` 与 `author/formal/human`

拒绝原因：

- 额外复杂度高
- 当前收益不足

## Decision

采用：

- `stage_root/author/draft`
- `stage_root/author/formal`
- `stage_root/review/request`
- `stage_root/review/result`
- `stage_root/review/closure`
- `stage_root/review/governance`

且本次重构为 **硬切换**，不保留旧路径兼容。
