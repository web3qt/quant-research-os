# QROS Progress Command Design

## Goal

新增一个研究员可直接使用的进度查看入口，让用户不必记住 lineage id 或误把 `qros-session` 当成“只读查询”命令，也能快速知道当前研究线推进到哪里、被什么 gate 卡住、下一步应该做什么。

## Confirmed Product Decision

新增能力采用两层入口：

- `qros-progress` skill：研究员在 Codex 中通过 `$qros-progress` 使用。
- `./.qros/bin/qros-progress` 命令：repo-local runtime wrapper，供 skill、人工诊断和脚本读取使用。

默认行为：

- 无参数时扫描当前 research repo 的 `outputs/`，选择最近修改的 lineage。
- 指定 `--lineage-id <lineage_id>` 时只查看该 lineage。
- 输出 `current_stage`、`current_skill`、`gate_status`、`blocking_reason`、`next_action`、`open_risks` 等核心字段。
- 整个命令必须只读，不写 artifact、不 scaffold、不推进 stage、不触发 confirmation。

## Scope

本次只做“最新研究进度查询”，不做 dashboard、HTML 展示、自动报告生成或跨 repo 聚合。

覆盖范围：

- 当前 repo 的 `outputs/<lineage_id>/`。
- mainline 与 `cross_sectional_factor` 两条现有 session route。
- 与 `qros-session --json` 当前状态字段保持一致。

不覆盖范围：

- 不替代 `qros-stage-display`。
- 不渲染阶段展示稿。
- 不执行 review。
- 不自动选择下一阶段。
- 不在没有 `outputs/` 或没有 lineage 时创建目录。

## Runtime Design

新增 `runtime/scripts/run_progress.py` 作为只读 CLI。

输入：

- `--outputs-root <path>`：必填，wrapper 默认传当前 repo 的 `outputs`。
- `--lineage-id <lineage_id>`：可选。
- `--json`：可选，输出 machine-readable JSON。

无 `--lineage-id` 时，runtime 只扫描 `outputs/` 下一层目录，选择最近有文件修改的 lineage 目录。选择结果需要在输出中显式展示，避免用户误解查询的是哪条线。

状态来源优先复用 `runtime.tools.research_session.run_research_session(..., lineage_id=...)`，但进度命令本身不能触发新 lineage 创建。无参数模式下只有当已有 lineage 目录存在时才调用 session 状态读取。

## Skill Design

新增 `skills/core/qros-progress/SKILL.md`。

触发条件：

- 用户问“最新研究进度”
- 用户问“现在到哪了”
- 用户问“当前卡在哪个阶段”
- 用户显式使用 `$qros-progress`

skill 行为：

- 优先运行 `./.qros/bin/qros-progress`。
- 如果用户给出 lineage id，传入 `--lineage-id`。
- 解释输出时明确区分 `current_stage`、`current_skill`、`gate_status` 和 `next_action`。
- 不把存在目录、placeholder 或 contract-only 文档描述成阶段完成。

## Documentation

更新用户入口文档：

- `README.md`
- `docs/guides/qros-research-session-usage.md`

文档需要把 `qros-progress` 定位为只读状态查询入口，并继续把 `qros-research-session` 保持为正式推进入口。

## Testing

最低验证要锁定这些行为：

- skill tree 中存在 `qros-progress`，且位于 `skills/core`。
- repo-local install 会写入 `bin/qros-progress`。
- `qros-progress` wrapper 引用 `run_progress.py`。
- 无 lineage 时命令失败为可理解错误，不创建 `outputs/`。
- 多 lineage 时默认选择最近修改的 lineage。
- `--lineage-id` 输出指定 lineage 的状态。
- `--json` 输出包含稳定字段。
- 文档中出现 `qros-progress` 入口。

修改触及 runtime/bin、skill 和用户入口文档，应运行 focused tests 与 smoke；若 session stage flow 语义未改变，不需要 full-smoke。
