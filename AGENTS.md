# QROS Agent Operating Contract

## Project Context

- 本仓库是 Quant Research OS 的流程、工具和治理规则仓，不是某条策略研究线的实现仓。
- 本仓库负责：workflow 规则、skills、文档、runtime wrapper、测试、artifact expectation。
- 本仓库不负责：用户某条 live lineage 的真实策略实现或长期保存正式研究产物。
- 真实研究程序、阶段执行代码和正式产物必须存在于消费 QROS 的 active research repo，通常是 `outputs/<lineage_id>/`。
- 不要因为目录存在、文件占位或只有合同说明文档，就宣称某个 stage 已完成。
- 必须明确区分：治理合同、机器可读产物、review closure、failure handling。

## Main Workflow

- 正常研究工作的统一入口是 `qros-research-session`。
- 当前第一阶段主流程覆盖：
  - `mandate_admission`
  - `mandate_freeze_confirmation_pending`
  - `mandate`
  - `data_ready`
  - `signal_ready`
  - `train_freeze`
  - `test_evidence`
  - `backtest_ready`
  - `holdout_validation`
- 每个阶段都必须先冻结要求的 grouped contracts，再真实物化 formal artifacts，之后通过 review 才能进入下一阶段。
- 如果 review verdict 不是正常放行，不要继续普通阶段推进，应当转入 failure handling。

## Important Directories

- `contracts/`：机器可读真值层，例如 schema、policy 和 stage gate。
- `skills/`：QROS skill 入口与分阶段行为。
- `runtime/tools/`：runtime helper、scaffold/build 逻辑。
- `runtime/scripts/`：命令行 wrapper 与确定性 task runner。
- `runtime/bin/`：稳定的用户入口，例如 `qros-session` 与 `qros-review`。
- `docs/`：SOP、使用说明、review 文档、操作文档。
- `tests/`：workflow 行为和文档回归测试。

## Directory Rules

目标文件路径祖先链上的 `AGENTS.md` 才会被自动纳入指令链。根目录启动时不会自动读取子目录规则；编辑子树前按需读取对应文件。

- `contracts/AGENTS.md`：真实 schema / policy / gate 规则。
- `skills/AGENTS.md`：真实 skill / workflow 规则。
- `runtime/AGENTS.md`：真实 runtime / helper / scaffold 规则。
- `docs/AGENTS.md`：真实文档目录规则。
- `tests/AGENTS.md`：真实测试目录规则。

## Commands

- 全量测试：`python -m pytest`
- 文档 / bootstrap 最小检查：`python -m pytest tests/contracts/test_agents_layout.py tests/bootstrap/test_project_bootstrap.py tests/docs/test_install_docs.py`
- smoke：`python runtime/scripts/run_verification_tier.py --tier smoke`
- full-smoke：`python runtime/scripts/run_verification_tier.py --tier full-smoke`
- 如果修改的是某个具体 stage runtime，先跑最小相关测试，再按需要扩大验证范围。

## Verification Rules

- 每个新需求默认都必须先定义并实际执行验证，不允许只写“已测试”而不给命令。
- 最低要求是 focused tests + smoke。
- 只要改动触及下列任一项，full-smoke 也必须跑：
  - `qros-research-session` stage flow / gate semantics
  - review / display / next-stage orchestration
  - route split / CSF routing
  - anti-drift snapshots 或 canonical session stage naming
  - stage-display supported stage contract
  - lineage-local stage-program auto-author seams
- `smoke` / `full-smoke` 的当前定义与命令以 `docs/guides/qros-verification-tiers.md` 和 `runtime/scripts/run_verification_tier.py` 为准。
- 如果任务是纯文档 / 纯图示且明确不改变 runtime / workflow contract，至少运行文档 / bootstrap 最小检查，并在最终报告里说明为什么没有跑 smoke / full-smoke。

## Working Rules

- 保持 diff 小、可审查、可回退。
- 优先修改 `skills/`、runtime helper、SOP 文档、schema 和测试。
- 复用仓库现有术语，不要为同一个 stage、artifact 或 contract 再发明第二套命名。
- 没有明确理由不要新增依赖。
- 当修改影响用户工作流、artifact contract 或 stage 语义时，必须同步更新测试和文档。
- 用户文档必须与当前 runtime 行为和测试夹具保持一致。
- 解释 freeze groups 时，优先以用户在磁盘上真实会看到的 runtime-facing field shape 为准。
- 如果正式 schema、枚举集合、字段语义或 stage gate 含义发生变化，必须同步清理 active skills、SOP、review checklist、`docs/show/` 图示和当前仍被引用的说明文档中的旧口径。
- 默认使用中文注释；尤其是 `runtime/tools/`、`runtime/scripts/`、`skills/` 里涉及各研究阶段实现、runtime gate、review/failure routing 的代码，新增注释应优先写成清晰、简短、面向维护者的中文说明。

## Safety Boundaries

- 未经用户明确同意，不得提交、合并或以任何方式把代码送入 `main` / `master`。
- 不要把 QROS 框架仓当作 active research repo 来写 live lineage 的真实策略程序或正式研究产物。
- 不要让 reviewer 直接写 runtime-owned closure / projection / audit 产物。
- 不要保留与当前 contracts、runtime 或 active skills 冲突的旧口径；若保留 legacy 表述，必须明确标注其只适用于旧 lineage 或 archived reference。

## Done Criteria

- 相关验证命令已经实际运行。
- 文档表述与当前 runtime 行为一致。
- 已扫描并处理 active docs / skills / SOP / diagrams 中与本次 workflow 或 artifact contract 冲突的旧口径。
- 最终报告里明确写出这次运行过的 focused tests / smoke / full-smoke。
- 如果仍有缺口，要明确写出，尤其是某条 route 或某个 stage 只做了部分覆盖时。

## References

- 统一研究会话：`docs/guides/qros-research-session-usage.md`
- review 约束地图：`docs/guides/qros-review-constraint-map.md`
- freeze group 字段说明：`docs/guides/stage-freeze-group-field-guide.md`
- 验证分层：`docs/guides/qros-verification-tiers.md`
- 安装与 repo-local runtime：`docs/guides/installation.md`
