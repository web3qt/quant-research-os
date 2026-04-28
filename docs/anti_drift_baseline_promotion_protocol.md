# QROS Anti-Drift 基线提升协议

这份协议定义 semantic-golden 与结构化回归基线如何被提升，同时不削弱 hard-fail 姿态。

## 作用域

适用于：

- canonical decision snapshot goldens under `tests/fixtures/anti_drift/`
- structured JSON regression payloads produced by anti-drift tools

## 核心规则

任何 baseline 都不得被静默覆盖。

任何变更后的 baseline 都必须经过：

1. 显式生成 diff
2. 人工 review semantic delta
3. 带 label 与 source note 的显式 promotion

## Deterministic 工作流

### 1. 生成当前 payloads

示例：

```bash
python runtime/scripts/run_research_session.py --outputs-root /tmp/qros_snapshot_verify --raw-idea "BTC leads high-liquidity alts after shock events" --snapshot > /tmp/current_snapshot.json
```

### 2. 对比 blessed baseline

使用 baseline 管理工具：

```bash
python runtime/scripts/anti_drift_baseline.py compare --baseline tests/fixtures/anti_drift --current /tmp/current_snapshots
```

如果 `matches=false`，当前分支会被阻塞，直到 delta 被修复或被显式 promotion。

如果要生成 nightly 的人类可读摘要，渲染 markdown report：

```bash
python runtime/scripts/render_anti_drift_nightly_report.py \
  --baseline tests/fixtures/anti_drift \
  --current /tmp/current_snapshots \
  --output /tmp/anti_drift_nightly_report.md
```

### 3. Review semantic delta

必答 review 问题：

- Did `route_skill` change?
- Did `stage_id` change?
- Did `formal_decision` change?
- Did `downstream_permissions` change?
- Did `blocking_reasons` change?
- Did the delta reflect an intentional contract change, not accidental drift?

### 4. 只提升有意图的 deltas

Promotion 命令：

```bash
python runtime/scripts/anti_drift_baseline.py promote \
  --current /tmp/current_snapshots \
  --baseline tests/fixtures/anti_drift \
  --label anti-drift-<date>-<reason> \
  --source-note "why this promotion is intentional"
```

该命令会在 promoted payloads 旁边写出 `baseline_manifest.json`。

## Release 姿态

- PR 只有在经过显式 review 后，才可以引入新的 goldens 或变更 baselines。
- Nightly regression 会把当前 payloads 与 blessed baselines 对比。
- Nightly regression 还应通过 `runtime/scripts/build_anti_drift_gate_summary.py` 输出 machine-readable gate artifact。
- Release assembly 应通过 `runtime/scripts/build_anti_drift_release_artifact.py` 消费 nightly gate artifact。
- 该流程的仓库 CI 入口是 `.github/workflows/anti-drift.yml`。
- 以下情况会阻塞 release：
  - 当前 payloads 与 blessed baselines 不同，但没有显式 promotion
  - newly blessed payloads 缺少 promotion manifest

## 有效 Promotion 的必要证据

- diff output
- semantic change 的原因
- promotion label
- promotion manifest
- 更新后的测试仍然通过

## 当前限制

- 这份协议当前只治理 JSON-based anti-drift payloads。
- 它还没有自动化 approval routing 或 PR annotations。
- 更广的 replay coverage 仍需扩展到第一批 semantic golden set 之外。
