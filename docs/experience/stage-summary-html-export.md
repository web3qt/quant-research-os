# Stage Summary HTML Export（PoC）

## 目的

这个导出面是一个 **`data_ready` 单阶段 v1 proof-of-concept**，用来验证：

- repo 自己的确定性 reflection 结构能否作为 stage summary 的 source of truth
- Codex subagent 是否适合扮演 **HTML 内容生成 worker**

它**不是**：

- 全阶段 dashboard
- `qros-session` 终端输出的替代品
- `--json` / `--snapshot` 的合同扩展

## 当前边界

- 只支持 `data_ready`
- 只在 `data_ready_next_stage_confirmation_pending`（也就是 mandatory display 已完成）之后导出
- 只消费 `02_data_ready/` 的确定性 reflection payload
- 不读取 parquet 内统计结果
- 缺失证据时保留 `missing` / `question` 提示
- subagent 只是 **Codex-time orchestration dependency**
  - 普通用户运行 repo runtime 时，不需要它

## 产物

脚本：

- `scripts/export_stage_summary_html.py`

核心模块：

- `tools/research_session_reflection.py`
- `tools/stage_summary_html.py`

## 两种 renderer

### 1. Deterministic fallback renderer

repo 自己根据规范化 payload 生成静态 HTML。

用途：

- baseline
- regression target
- subagent 不可用时的 fallback

输出示例：

- `outputs/<lineage>/reports/data_ready_summary.deterministic.html`

### 2. Subagent bundle

repo 不在 Python runtime 里直接调用 Codex subagent，而是导出一个 **handoff bundle**：

- `payload.json`
- `prompt.txt`
- `output_path.txt`

用途：

- 让 Codex 在 orchestration 时读取同一份 payload
- 按保守、证据驱动边界生成 HTML 页面

输出目录示例：

- `outputs/<lineage>/reports/data_ready_summary.subagent_bundle/`

## 用法

### 同时导出 deterministic HTML + subagent bundle

```bash
python scripts/export_stage_summary_html.py \
  --outputs-root <outputs_root> \
  --lineage-id <lineage_id> \
  --renderer both \
  --json
```

### 只导出 deterministic HTML

```bash
python scripts/export_stage_summary_html.py \
  --outputs-root <outputs_root> \
  --lineage-id <lineage_id> \
  --renderer deterministic
```

### 只导出 subagent bundle

```bash
python scripts/export_stage_summary_html.py \
  --outputs-root <outputs_root> \
  --lineage-id <lineage_id> \
  --renderer subagent-bundle
```

## 建议验证方式

1. 先看 deterministic HTML 是否和当前 terminal reflection 语义一致
2. 再让 Codex subagent 基于同一份 `payload.json` + `prompt.txt` 生成 HTML
3. 对比：
   - section order
   - `missing` / `question` 是否被保留
   - 是否出现 payload 里没有的 invented claims

## 与 `qros-session` 的关系

这个 PoC **不修改**：

- `qros-session` 的终端文本输出
- `qros-session --json`
- `qros-session --snapshot`

也就是说，这是一条**独立导出路径**，不是现有 session surface 的合同替换。
